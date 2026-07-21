# v1 Capability Parity Matrix

> Baseline scope: legacy implementation on the `refactor` branch. This document records observable behavior, not the v2 design. It is the acceptance reference for later migration; a v2 implementation may change an internal mechanism only when the stated caller-visible contract is preserved or an explicit R-D decision retires it.

## Status and reading rules

- **Source baseline:** commit `5e6e892` (`docs(refactor): add v2 rewrite plan`).
- **In scope:** currently implemented behavior in `main.py` and `src/`.
- **Out of scope / retired by R-D6:** migration of old sessions, memories, Chroma indexes, `data/temp/`, input history, plans, handoff state, and dump/log state.
- **Error convention:** tool handlers raise `ToolCallException` for correctable caller errors; `BaseAgent` turns it and unexpected exceptions into a structured tool-call result for the model. Approval rejection and cancellation are represented by legacy sentinel payloads.
- **Parity rule:** “same capability” does not require retaining v1 global registries, magic dictionaries, private-field access, or import-time side effects. Those mechanisms are explicitly replaced by the v2 architecture.

## Application and interaction baseline

| Capability | Input | Output | Side effects | Failure / edge behavior | v2 disposition |
|---|---|---|---|---|---|
| CLI conversation | User text; `Request(USER_INPUT)` then `CONTINUE` internally | Rendered final Markdown or progress update | Keeps per-agent history; auto-saves on `FINISH`; optionally starts memory extraction | EOF/Ctrl+C exits outer loop; malformed model output gets one repair attempt | Migrate |
| Main-to-sub-agent handoff | Main model calls `switch_to_subagent(agent_name, context)` | Main pauses; selected sub-agent becomes active | Stores switch call id; later injects summary as the matching tool result | User approval is required; unknown registry key is rendered as an error | Replace with typed handoff |
| Sub-to-main return | Sub model calls `switch_to_mainagent(summary)` or user sends `/exit_sub` | Main resumes with summary context | Saves main state and schedules sub-save cleanup | `/exit_sub` is invalid while main is active | Replace with typed handoff |
| User selection | `provide_choices(question, choices)` | Selected or custom user text in tool result | Blocks worker through `UIBridge` while CLI renders questionary UI | Selection is UI-dependent | Replace with typed selection event |
| Tool approval | Tool metadata plus `TOOL_CONFIRM_ENABLED` | Approved execution or rejected result | CLI/UIBridge blocks for confirmation | `NEVER`, `ALWAYS`, `CONFIG` policies; rejection closes the legacy tool call | Migrate policy; replace UI bridge |
| Cancellation | Esc during agent loop | Cancelled tool result / cancelled loop state | Module-level cancellation event is set then cleared at a new request | Checks occur before LLM, after LLM, and before a tool; later requests should remain usable | Migrate behavior; replace global event |
| Help and commands | `/help`, `/edit`, `/dump`, `/restore [id]`, `/rewind`, `/ragreload [target]`, `/build-memory`, `/exit_sub`, `/auto-approve-switch`, `/exit` | Rendered command result or next request | Editor launches a temporary file; restore rewrites handler state; reload triggers RAG load | Missing editor returns empty input; invalid restore is reported; `/exit` ends the CLI | Migrate |
| Session save/restore/rewind | Agent history, plan, session id; optional selected rewind point | JSON save data; restored active conversation; prefilled input | Writes `data/save/{session_id}`; restores main/sub histories and plans | Save failure is logged; missing/bad session is reported; rewind truncates history before re-submission | Migrate fresh v2 schema; no v1 migration |
| Conversation dump | Current agent history | Dump path or failure indication | Writes a timestamped message dump under `data/logs/` | Failure returns false and is logged | Migrate |

## Agent, prompt, and model baseline

| Capability | Input | Output | Side effects | Failure / edge behavior | v2 disposition |
|---|---|---|---|---|---|
| Main routing | User request and registered sub-agent descriptors | Main answer or a handoff tool call | Reads global `AgentRegistry` prompt data | No direct domain work by design; unknown target is rejected by the app | Migrate declarative spec |
| Resume specialization | Resume/JD request and workspace tools | Resume guidance, file/tool calls, or return summary | Operates only through tools; uses LaTeX-template prompt data | Must read before precise edit; tool/compile errors are fed back to the model | Migrate in R7 |
| Job-search specialization | Job-search request | Model response / tool use | Registered at startup | Current test/slice agent only; complete product behavior is frozen | Keep baseline, defer product expansion |
| Prompt rendering | Prompt name plus 14 agent variables | Combined general-agent and agent prompt text | Reads `data/prompts/` | Missing prompt or unresolved/missing variables fail load/render | Migrate renderer and preserve static assets |
| LLM chat | OpenAI-compatible messages, tool XML, tier parameters | Parsed JSON model response and optional thinking | Lazy thread-safe client singleton; provider thinking settings | Provider/parse/format errors enter agent repair or failure path; thinking is stripped before later model input | Migrate adapter behavior |
| Web search | Natural-language query | Search-derived text | Uses the LLM client’s web-search method | Provider failure becomes a tool failure | Migrate / redefine adapter |

## Tool catalog baseline (25 tools)

Tool visibility is currently implicit: common tools are visible to all, `agent=["main"]` is main-only, `agent=["*"]` means sub-agents, and resume workspace tools are resume-only. `N` = never ask approval; `A` = always ask; `C` = follow configuration.

| Tool | Input → output | Side effect | Failure / constraint | Approval | v2 disposition |
|---|---|---|---|---|---|
| `get_current_datetime` | none → local timestamp with offset | None | System clock only | N | Migrate |
| `get_working_dir` | none → absolute workspace path | Creates configured working directory if missing | Filesystem error propagates | N | Migrate |
| `web_search` | query → search text | Remote model/search request | Provider failure | C | Redefine adapter |
| `switch_to_subagent` | target key, context → switch sentinel | Requests handoff | Main only; target must resolve later | A | Replace |
| `switch_to_mainagent` | summary → switch sentinel | Requests return handoff | Sub-agent only | A | Replace |
| `provide_choices` | question, choices → selected text | Blocks on `UIBridge.select()` | UI cancellation/availability | N | Replace |
| `create_plan` | item descriptions → full plan state | Replaces current plan; first item becomes active | Requires current-agent global context | N | Migrate to service |
| `update_plan_status` | item id, status → full plan state | Changes item; may activate next item | Valid statuses: pending/in_progress/completed/cancelled | N | Migrate to service |
| `cancel_all_plans` | none → empty/completed plan result | Cancels unfinished items | Requires current-agent global context | N | Migrate to service |
| `replan` | replacement unfinished items → full plan state | Retains completed work, replaces remainder | Requires current-agent global context | N | Migrate to service |
| `workspace_read` | relative path, offset, limit → numbered text lines | Marks file as read in process cache | Workspace-only; file must be readable text | N | Migrate |
| `workspace_list` | relative directory → entries | None | Workspace-only; path must be directory | N | Migrate |
| `workspace_grep` | pattern, path, glob, regex, limit → matches | None | Workspace-only; pattern/encoding errors | N | Migrate |
| `workspace_search_file` | filename glob, path, limit → paths | None | Workspace-only; capped results set `truncated` | N | Migrate |
| `workspace_replace` | file, old text, new text → replacement count | Rewrites file in UTF-8 | File only; does not itself enforce the documented prior-read rule | C | Migrate, strengthen atomicity |
| `workspace_write` | new relative path, content → written flag | Creates parent directories and file | Refuses overwrite; workspace-only | C | Migrate, atomic write |
| `workspace_delete` | relative paths → deleted paths and per-path errors | Deletes files or empty directories | Partial success allowed; non-empty directory refused | C | Migrate |
| `workspace_move` | source, destination → moved flag | Moves/renames and creates parent dirs | Source must exist; destination must not | C | Migrate |
| `workspace_edit` | file and line/old-content edits → applied results | Rewrites file | Must have a prior `workspace_read`; any line mismatch/error aborts before write | C | Migrate, session-scoped revision |
| `workspace_open` | existing file → opened flag | Launches OS default opener | Missing file or OS launch failure | C | Migrate through frontend adapter |
| `read_customer_file` | external path, offset, limit → numbered text/PDF/DOCX content | Reads user-provided file outside workspace | Must exist and use a supported/readable format | C | Migrate with explicit grant boundary |
| `query_memory` | query, optional `fact`/`preference`, top-k → chunks | Queries Chroma memory collection | RAG must be ready; invalid type raises `ToolCallException` | N | Port adapter until R6 |
| `query_reference_data` | query, optional reference category, top-k → chunks | Queries Chroma reference collection | RAG must be ready; invalid category raises `ToolCallException` | N | Port adapter until R6 |
| `copy_template` | template, prefix, optional target dir → copied artifact paths | Copies LaTeX template files and README | Invalid template/name/path or destination collision | C | Migrate in R7 |
| `build_pdf` | relative `.tex` path → compile result/PDF path | Runs `pdflatex`, produces auxiliary/PDF files | Missing source/compiler, nonzero exit, timeout/compile error | C | Migrate through process/artifact service |

## Data and lifecycle baseline

| Capability | Input | Output | Side effects | Failure / edge behavior | v2 disposition |
|---|---|---|---|---|---|
| Reference RAG | `data/reference/` files, optional reload target | Searchable reference chunks | Starts model/index loading in a background thread; indexes Chroma | `is_ready()` guards query tools; loading errors are logged/reported | Migrate in R6 |
| Memory | Agent conversation and memory-builder prompt | Markdown facts/preferences and retrieval results | Writes per-agent files under `data/memories/`; indexes asynchronously | Index failure is logged; shutdown waits for pending work | New repository only; do not migrate data |
| Static assets | Prompt files, reference files, resume templates | Inputs consumed by application | Read-only project assets | Missing/corrupt asset causes relevant load/tool failure | Preserve as v2 inputs |
| Logging/lifecycle | Logger calls and registered shutdown hooks | Rotating app log and ordered cleanup | Writes `data/logs/app.log`; shutdown runs hooks in reverse order | Defensive failures log rather than abort cleanup | Migrate |

## Explicit legacy mechanisms that are not parity requirements

The following are behavioral implementation details intentionally excluded from v2 parity: mutable module-level `ToolRegistry`, `AgentRegistry`, current `UIBridge`, current-plan agent global, workspace read cache, lazy module facades, import-time tool registration, CLI reads/writes of agent private fields, and magic `__switch__`, `__reject__`, and `__cancelled__` dictionaries. Their caller-visible outcomes are covered above and must be represented with explicit v2 composition, services, and typed runtime events.
