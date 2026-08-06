# 任务列表

> 适用分支：`main`。架构目标见 `docs/design.md`，里程碑见 `docs/plan.md`。

## 状态说明

| 标记 | 状态 | 说明 |
|------|------|------|
| ⬜ | 待开始 | 尚未开始 |
| 🔄 | 进行中 | 当前正在处理；全表同时只能有一个 |
| ✅ | 已完成 | 已实现并通过对应门禁 |
| ⏸️ | 阻塞 | 受外部条件或用户决策阻塞 |
| ⛔ | 终止 | 不再实施，并应注明替代任务 |
| 📌 | 暂缓 | 仍有效，但推迟到后续阶段 |

## R0 —— 基线冻结与决策门禁

### 1. 现状研究

- ✅ 读取 `docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md` 和相关 decision。
- ✅ 盘点 CLI、LLM、Agent、Tool、Plan、Session、RAG、Memory、Workspace、Resume 当前能力。
- ✅ 区分已实现、测试壳、路线图未完成、方案取消和架构受限能力。
- ✅ 定位 BaseAgent/App 巨型对象、跨层私有访问、全局状态、导入副作用和魔法控制字段。
- ✅ 统计当前实际工具数为 25，并记录与文档 23 的漂移。
- ✅ 形成 `docs/design.md` 与 `docs/plan.md`；历史 v1 内容由 Git 保留。

### 2. 用户决策

- ✅ 用户确认 R-D1：在 `src/get_me_in/` 受控重写。
- ✅ 用户确认 R-D2：当前架构禁止可变全局单例和 import-time 注册。
- ✅ 用户确认 R-D3：采用 RuntimeCommand/RuntimeEvent 强类型协议。
- ✅ 用户确认 R-D4：Resume 保留直接编辑 LaTeX，增加 Workspace/Artifact service。
- ✅ 用户确认 R-D5：授权核心自动化测试。
- ✅ 用户确认 R-D6：不迁移旧运行数据，仅保留 reference/prompts/resume templates。
- ✅ 旧 Session、Memory、Chroma、temp、Plan、handoff 和 input history 可直接废弃。

### 3. 基线材料

- ✅ 建立 capability parity matrix，逐项列出输入、输出、副作用和失败行为。
- ⛔ 选取 v1 Session 样例用于 migration —— 不迁移旧会话，已由 R-D6 终止。
- ⛔ 选取旧 Memory/Workspace 样例用于 migration —— 不迁移旧运行数据，已由 R-D6 终止。
- ✅ 核对 `data/reference/`、`data/prompts/`、`data/resume/template/` 的新架构输入边界。
- ✅ 建立 CLI smoke checklist。
- ✅ 记录旧入口可运行的基线 commit。
- ✅ 完成 G0 审查；未通过前不创建新架构代码文件。

## R1 —— 架构骨架与 Composition Root

> 开始前先向用户列出本阶段所有新文件、类和公开方法，确认后再创建。

### 1. 包结构与依赖规则

- ✅ 创建 `src/get_me_in/` 分层目录。
- ✅ 定义新架构 import 规则：domain → 无外部 adapter；application → domain/ports；adapter → ports；CLI → application。
- ✅ 增加开发期依赖检查方式，确保新架构不 import 旧 BaseAgent/App/UIBridge/Registry。
- ✅ 清理源码树中的 `.ipynb_checkpoints` 方案，实际删除留到 R8。

### 2. Settings 与基础 ports

- ✅ 设计 typed Settings 字段、解析、必填校验和错误返回。
- ✅ 保留 `config` 在第三方模型 import 前设置 HF 环境的能力，但移除业务模块 import 时 `sys.exit()`。
- ✅ 定义 Clock、IdGenerator、LLMPort、SessionRepository 最小协议。
- ✅ 创建实例级 CancellationToken。

### 3. 声明式 Agent 与 Prompt

- ✅ 定义 AgentKey、Capability、AgentStyle、AgentSpec。
- ✅ 定义 AgentDescriptor 与 AgentCatalog。
- ✅ 定义 PromptRenderer，复用现有 `data/prompts/general_agent/` 模板。
- ✅ 将 MainAgent 14 个方法转换为一个声明式 spec。
- ✅ 明确 prompt 模板缺失变量和多余变量的错误类型。

### 4. Composition Root

- ✅ 设计 `build_application(settings)` 方法清单。
- ✅ 显式创建所有 service/catalog/adapter，不使用导入副作用。
- ✅ 确认构造两个 Application 实例不会共享 history、registry、cancel 或 session id。
- ✅ 完成 G1 验收。

## R2 —— Agent Runtime 与事件协议

### 1. Domain event

- ✅ 定义 provider-neutral ConversationRecord union 与 Role；不再使用 ConversationEvent/EventKind。
- ✅ 定义 RuntimeCommand：UserMessage/Continue/Approve/Reject/Selection/Cancel/ToolResult。
- ✅ 定义 RuntimeEvent：Progress/Approval/Selection/ToolStarted/ToolFinished/Handoff/Completed/Failed/Cancelled。
- ✅ 删除新架构中对 `__switch__`、`__reject__`、`__cancelled__` 的需求。

### 2. Agent state machine

- ✅ 定义 RuntimeState 和单一 phase 枚举，替代 `_pending_tool/_pending_switch/_pending_reject` 组合；R4 将其并入 AgentSessionState。
- ✅ 实现 user input → LLM → finish 基本路径。
- ✅ 实现 tool call → pause → tool result → LLM 路径。
- ✅ 实现 output format 修复与最多一次格式提示注入。
- ✅ 实现 unknown tool、max rounds、timeout 和 provider failure。
- ✅ 提取 ModelReplyParser；domain Message 不直接解析 provider 字符串。
- ✅ 保证 thinking 不写回下一轮模型输入。
- ✅ 将当前 Agent 可见的 ToolCatalog 与 AgentCatalog 描述注入 Prompt，禁止依赖 Fake LLM 硬编码工具调用。
- ✅ 定义 provider-neutral message codec，显式保存 tool name、arguments、call id 与结果关联；Handoff 必须携带原 tool call id。
- ✅ 限制 WAITING_FOR_TOOL 阶段可接受的 command；Cancel、新 UserMessage、Reject 与 Handoff 均不得遗留孤立 TOOL_CALL。
- ✅ 支持单次用户请求中的连续多工具回合，并使 max rounds 与 `Settings.llm_timeout_seconds` 可配置且真实生效。

### 3. LLM adapter 与取消

- ✅ 定义 LLMRequest/LLMResult/ModelProfile。
- ✅ 实现 OpenAI sync adapter，集中 pro/flash/provider thinking 配置。
- ✅ 设计并实现活动调用 handle 的 cancel/close/reset 生命周期。
- ✅ 使用真实阻塞 adapter 验证调用执行中可取消，且下一次调用仍可继续；Fake LLM 仅作 unit test。
- ✅ 禁止 Runtime 访问 OpenAI SDK 私有 transport。
- ✅ 重新完成 G2 验收；86 项核心自动化测试通过，临时 Runtime Runner 已完成人工可用性验证。

## R3 —— Tool Runtime、Plan 与 Workspace

### 1. Tool Catalog

- ✅ 定义 ToolDefinition、ToolSchema、ToolPolicy、ToolContext、ToolOutcome。
- ✅ 将 decorator 改为仅创建定义，不自动写全局 Registry；或改为显式 builder。
- ✅ 为全部工具绑定明确 capability，并验证 Main Agent 不可见 workspace/resume/retrieval 等领域工具。
- ✅ ToolCatalog 提供目录导出，使文档/诊断可看到真实工具数。
- ✅ 统一参数过滤、必填校验、业务错误和框架错误。
- ✅ 完整处理审批、拒绝、取消、新用户输入与 handoff 的 call closure，并增加 pending 状态转换测试。

### 2. Plan

- ✅ 将 Plan/PlanItem/PlanStatus 提取为 domain model。
- ✅ 将 create/update/cancel/replan 移入 PlanService。
- ✅ ToolContext 注入 PlanService，删除 `_plan_agent`。
- ✅ 保证同一 plan 最多一个 IN_PROGRESS。
- ✅ 定义 Plan snapshot/restore codec。

### 3. Workspace

- ✅ 定义 WorkspacePort 与 LocalWorkspace。
- ✅ 使用 `Path.is_relative_to(root)` 做边界检查。
- ✅ 集中编码检测、文本行模型、glob/search 和结构化错误。
- ✅ 写入与编辑使用原子文件替换。
- ✅ 将 read-before-edit 授权绑定到 session/tool context；纯内容 hash 不得跨 Session 复用为编辑授权。
- ✅ 移除进程级 `_read_files`。
- ✅ 定义批量删除部分成功的结果类型。
- ✅ 使 ProcessRunner 在子进程执行期间支持 cancel/terminate，而不只在 `subprocess.run()` 前后检查 token。

### 4. 现有工具归类

- ✅ 迁移 2 个 system tools。
- ✅ 迁移或重新定义 web_search tool。
- ✅ 以 typed handoff/interaction 替代 3 个 switch tools 的控制逻辑。
- ✅ 迁移 4 个 Plan tools。
- ✅ 迁移/合并 10 个 workspace tools，保持外部功能等价。
- ✅ 迁移 read_customer_file，明确外部路径授权边界。
- ✅ 暂以 port adapter 迁移 2 个 RAG query tools，R6 再替换实现。
- ✅ 迁移 copy_template/build_pdf，R7 接入 ArtifactService。
- ✅ 输出完整的 25 工具迁移矩阵。
- ✅ 重新完成 G3 验收；86 项核心自动化测试通过，临时 Runtime Runner 已完成人工可用性验证。

## R4 —— Session Aggregate 与编排

### 1. Session model

- ✅ 定义 `AgentSessionState`、`SessionState`、`HandoffFrame`、`SessionTurnView`、`SessionView`、`SessionPreview`；R4 不提前定义 Artifact schema。
- ✅ 将现有 RuntimeState 的 history/phase/pending/model-call/repair 状态并入 AgentSessionState，SessionState 成为唯一规范状态源。
- ✅ AgentRuntime 改为 `advance(state, command) -> RuntimeTransition`，不得保留第二份长期状态；Application 对外仍一次返回一个 RuntimeEvent。
- ✅ 每个 Application 同时只管理一个活动 Session；生成真实 session id，并按 session/agent 构造 ToolContext、CancellationToken、Plan 绑定与 WorkspaceAccessState。
- ✅ Settings 增加 `sessions_dir`，默认使用全新 `data/runtime/sessions/`，不得读取旧 `data/save/`。
- ✅ CLI input history 留在 R5 InputController，不进入 domain SessionState；R5 复审决定不增加独立持久化 schema，restore 后从 SessionView rewind_points 重建。
- ✅ 提供公开 `view/snapshot/restore/rewind(turn_id)/list_sessions/dump` API。
- ✅ 禁止 CLI 直接访问 `_history`、`_plan` 或 Agent 私有方法。

### 2. Orchestrator

- ✅ 实现 Hub-and-Spoke 路由约束。
- ✅ Main Runtime 只注入可路由 descriptor；子 Agent Runtime 不持有完整 AgentCatalog。
- ✅ 定义 `CompleteHandoff` 与 `FailHandoff`，使 WAITING_FOR_HANDOFF 可以按原 call id 闭合。
- ✅ 实现带 turn_id/call_id 的 main→sub handoff frame。
- ✅ 切换到子 Agent 时以 handoff context 启动目标 Runtime，正式 CLI 后续只需继续驱动 active agent。
- ✅ 实现 sub→main summary、frame pop、active agent 恢复与源 tool call 原子闭合。
- ✅ 实现 `/exit_sub` 的 application command，不向 Agent 私有 history 直接 append。
- ✅ 处理未知 Agent、目标启动失败、嵌套切换、子 Agent 失败/取消和中断中的 handoff；所有失败路径均闭合原 call id。
- ✅ 使用测试专用 sub Agent 完成 G4；真实 Resume AgentSpec 不提前从 R7 移入。

### 3. Snapshot repository

- ✅ 定义 `schema_version=2` SessionSnapshot DTO。
- ✅ 每条 ConversationRecord 增加 turn_id；rewind 只允许用户回合边界，不截断在 tool call/result 中间。
- ✅ 分离 provider-facing ConversationCodec、磁盘 SessionSnapshotCodec 与 JSON file repository。
- ✅ 明确定义可恢复稳定 phase；活动 LLM/Process 归一化为 interrupted/cancelled，禁止自动重放 TOOL_READY 副作用。
- ✅ 原子写入并报告保存失败；保存失败不得触发旧 sub 数据清理。
- ⛔ 实现 legacy session/meta/message/plan migration —— R-D6 明确不迁移。
- ✅ 实现 list、preview、dump。
- ✅ Restore/Rewind 同步修正 pending action、plan 和 handoff stack，并清除 WorkspaceAccessState，编辑前重新读取。
- ✅ Restore 在替换当前 Session 前拒绝未装配 Agent；snapshot 校验 handoff frame 与 active agent、源 pending call 和 turn id 一致。
- ✅ 增加 Session、Orchestrator、Snapshot codec 与 JSON repository 的核心自动化测试文件，覆盖 G4 失败路径。
- ✅ R5 前复审补齐 handoff 启动/取消/嵌套、复杂 rewind、workspace grant 清理、损坏 snapshot 与公开 rewind projection 测试。
- ✅ 完成 G4 复验（104 项核心自动化测试通过）。

## R5 —— CLI 拆分与交互迁移

### 0. 启动前复审门禁

- ✅ G4 完成并 checkpoint 后，基于实际 Application/Session/Command/Event/cancellation API 重新 Review R5～R8。
- ✅ 复核 R5 CliApp、CommandRegistry、InputController、Renderer、WorkerRunner 的职责和新文件/公开方法清单，确保 CLI 不吸收业务编排。
- ✅ 复核 R6 命令接入与资源清理、R6/R7 并行及验收依赖、R8 删除/回退/临时 Runner 清理范围。
- ✅ 将复审结论与 R5 清单同步到活跃 design/plan/task/decision。
- ✅ 用户已确认 `docs/design.md#67-cli` 的 R5 新文件、类与公开方法清单；允许在新会话按清单开始编码。

### 1. CLI shell

- ✅ 第一实施切片：创建 `commands.py` 与 `test_cli_commands.py`，固定强类型 command spec/result、解析、alias、replace 和核心 command handlers；110 项核心自动化测试通过，独立提交 `151b04a`。
- ✅ 创建 CliApp，仅保留输入循环和 application command/event 转发；覆盖 handoff continue、审批、终态自动 snapshot 与保存失败提示。
- ✅ 创建 CommandRegistry，命令帮助与 handler 同源。
- ✅ 创建 InputController，管理 autocomplete/history/prefill/editor；使用 `set_completions(CompletionProvider)` 动态读取 CommandRegistry 的最新补全。
- ✅ 创建 Renderer，管理 Markdown/Plan/spinner/error/recap。
- ✅ 创建 WorkerRunner，使用单 worker 串行调用 Application，跨线程只调用公开 `request_cancel()`；覆盖并发拒绝、取消与关闭。
- ✅ 创建 `cli/__init__.py`、`cli/main.py` 与 `cli/__main__.py`，提供 `python -m src.get_me_in.cli` 独立入口；保持旧 `main.py` 不变。

### 2. 命令迁移

- ✅ `/help`；从当前注册表按命令名排序，列出 alias 与参数说明。
- ✅ `/edit`
- ✅ `/dump`
- ✅ `/restore [session_id]`；无参数时显示序号、最新用户输入预览与保存时间，通过 InputController 选择 session 并映射回 session_id；列表末尾提供“❌ 取消”，取消时直接返回 CLI 且不调用 Application。
- ✅ `/rewind`；无参数时显示序号与用户输入预览，通过 InputController 选择公开 rewind point，并映射回精确 turn_id；列表末尾提供“❌ 取消”，取消时直接返回 CLI 且不调用 Application；回退前保存目标文本，成功后预填到下一次 CLI 输入框，不能从回退后的投影反查目标。
- ✅ `/ragreload [target]`：R5 先注册并明确报告 R6 尚不可用，R6 再接真实 handler。
- ✅ `/build-memory`：R5 先注册并明确报告 R6 尚不可用，R6 再接真实 handler。
- ✅ `/exit_sub`；`ExitSubAgent` 返回的 RuntimeEvent 通过 `CommandAction.DRIVE` 交回 CliApp，`ToolFinished` 会继续发送 `Continue` 直至终态；主 Agent 下的无效调用以可读错误返回输入框。
- ✅ `/approval`；无参数切换 `prompt/auto`，或用参数显式设置；策略只决定 ApprovalRequested 是否自动 Approve，且不保留 `/auto-approve-switch`。
- ✅ `/exit`

### 3. Interaction 与跨平台

- ✅ ApprovalRequested → questionary 选项列表“✅ 执行 / ❌ 取消” → Approve/Reject command；不得使用 `y/N` 确认框。`Reject` 写入拒绝结果闭合 call 后以 `Cancelled` 结束当前内层循环并归还输入框，实际工具失败仍交回模型；代码、自动化验证与人工 smoke 已完成。
- ✅ SelectionRequested → 选择/自定义输入 → SubmitSelection command；代码、自动化验证与人工 smoke 已完成。
- ✅ 删除 UIBridge 和模块级 current bridge 的新架构依赖。
- ✅ Windows UTF-8、Esc、Ctrl+C、EOF 和 editor-not-found 行为验证。
- ✅ Input history 使用进程内 CLI-owned state；restore 后从 `SessionView.rewind_points` 重建，不增加独立持久化 schema；人工 smoke 已通过。
- ✅ Completed/Failed/Cancelled 后自动 snapshot；保存失败单独渲染且不得覆盖原终态。
- ✅ HandoffRequested 后发送 Continue，验证目标 Runtime 已由 Orchestrator 启动。
- ✅ 工具开始显示脱敏参数摘要，工具结束显示截断结果预览；Plan 工具结束后显示只读 Plan 表格，不解析工具输出字符串。
- ✅ 命令 handler 的预期异常由 CliApp 统一渲染，`/restore`、`/rewind`、`/exit_sub` 等无效参数或状态不会终止 CLI；补充 CommandRegistry → CliApp → Continue 的跨组件回归测试。
- ✅ G5 通过后删除临时 `scripts/v2_runtime_smoke.py`。
- 📌 Sticky Plan：Renderer 稳定后评估，默认不阻塞 G5。
- ✅ 完成 G5 验收并通过审查修复复验；用户确认 V50–V56 人工 smoke 可接受，134 项核心自动化测试与 CLI 编译验证通过，DeepSeek Web Search 最小 provider smoke 已通过。

## R5-F —— LLM `thinking` 契约修复

### 1. 输出、domain 与事件契约

- ✅ 对齐 OutputFormat（当前文件名为 `08_output_format.md`）：finish 必须包含非空 string `message`，`thinking` 可省略；省略、`null`、空字符串或空白字符串均表示没有摘要，其他非空值必须是 string。tool_call 可省略 thinking；missing/type error 注入“具体错误 + 完整 canonical output format”并最多修复一次。
- ✅ 为 assistant `MessageRecord` 与 `ToolCallRecord` 增加可选 thinking；user/system/tool result 不产生 thinking。
- ✅ AgentRuntime 不再丢弃 `ModelReply.thinking`；Completed 通过 MessageRecord、ToolStarted 通过显式字段向前端投影。
- ✅ 保持 provider-neutral 边界：不得读取或保存 OpenAI/DeepSeek 原生 `reasoning_content`。

### 2. 上下文、snapshot 与展示

- ✅ ConversationCodec 对所有历史记录剥离 thinking，补齐多轮 finish/tool call 不回放测试。
- ✅ SessionSnapshotCodec 对 assistant message/tool call thinking 做可选 round-trip；缺失字段兼容为 `None`，不迁移 v1 Session。
- ✅ Settings 增加 `show_thinking` 并读取 `SHOW_THINKING`；不得与只控制 provider 的 `llm_thinking_enabled` 混用。
- ✅ Renderer 在 show_thinking=true 且摘要非空时展示“思考摘要”，覆盖 Completed 与 ToolStarted；关闭时不展示但保留记录；最终回复先显示摘要再显示 LLM message。

### 3. 范围与 G5-F

- ✅ 初始 G5-F 只修改既有协议、Runtime、snapshot、Settings、Renderer 与测试；真实 CLI 复验后以独立 follow-up 新增 `logging_setup.py`，恢复显式日志装配与格式失败诊断，未进入 R6 范围。
- ✅ 运行完整核心自动化测试、CLI 编译与 SHOW_THINKING 开／关 smoke，独立提交修复证据：`da530dc`、`937c4ea`、`123281d`、`abae597`；最终 146 项核心测试通过，真实 CLI 启停日志 smoke 通过。
- ✅ 已执行 `/project-checkpoint` 保存 G5-F 及 follow-up 结论；R6 coding 现可按已确认清单启动。

## R6 —— Knowledge/RAG 与 Memory

> ✅ R6-F 已完成并重新通过 G6：启动、取消、索引一致性、后台失败可见性、资源关闭和测试进程退出问题均已修复。该阶段随后停在 R6-T；决策 177 已在后续会话确认 R7 总体边界。

### 0. 启动确认与范围

- ✅ 基于 R5 修复后的 Application/CLI/Worker/Session 边界重新审查 R6。
- ✅ 删除重复 SearchQuery/SearchResult、v1 RagLoader Facade、MemoryService.search、observer/delayed import/daemon thread 等设计。
- ✅ 增加 ApplicationCommand RUN path、MemoryBuildSource、ResourceStack、BackgroundWorker、versioned manifest 和 R6-T 终止门禁。
- ✅ 记录 R6 新文件、对象、构造依赖和公开方法清单，并按该清单完成 R6 代码。
- ✅ 用户已确认 `docs/design.md#69-knowledge-与-memory` 的 R6 清单；在完成 G5-F checkpoint 后实施并完成 R6 coding。

### 1. Domain、ports 与 manifest diff

- ✅ 第一切片创建 `domain/knowledge.py`、`domain/memories.py`、`ports/knowledge.py`、`ports/memories.py` 与 `test_knowledge_service.py`，实现并独立提交 domain/ports/manifest diff 纯逻辑。
- ✅ 保留 R3 tool-facing RetrievalPort/RetrievalResult；仅增加 index 内部 IndexHit，未建立第二套公开搜索 DTO。
- ✅ 定义 manifest schema_version、source key、observed/indexed hash、mtime、chunk ids、status、pending operation 与 error。
- ✅ 实现纯逻辑 scan diff：新增、修改、删除、同 hash 重命名、失败后重试和幂等 no-op。
- ✅ 固定当前路径：`data/runtime/knowledge/manifest.json`、`data/runtime/knowledge/chroma/`、`data/runtime/memories/`；未读取旧 Chroma/Memory 数据。

### 2. Application command 与资源生命周期

- ✅ 增加 `ApplicationResult`、`CommandAction.RUN` 与 command payload；WorkerRunner 串行执行 RuntimeCommand/ApplicationCommand，CliApp 只渲染 typed result。
- ✅ 增加 `ReloadKnowledge`、`BuildMemory`；`/ragreload` 可取消，`/build-memory` 只排队并立即返回 receipt。
- ✅ 增加 `SessionService.memory_source()`，复制当前 Agent 的 immutable ConversationRecord 并将 assistant/tool call thinking 规范化为 `None`；CLI/后台线程不访问 SessionState/private history，MemoryExtractor 不接收展示摘要。
- ✅ 增加单非 daemon BackgroundWorker；前台 reload 与后台 memory 使用独立 cancellation。
- ✅ 增加 ResourceStack 与 CloseReport；只注册顶层 owner，逆序、幂等、失败隔离并报告 timeout。
- ✅ 增加 `Application.finalize_turn()`，先 snapshot，再按 typed auto-memory setting 可选排队；Memory 失败不覆盖原终态或 snapshot。

### 3. KnowledgeService 与 adapters

- ✅ 以 fake source/chunker/index/manifest 完成 KnowledgeService contract：state、search、reload、index_document、delete_source、busy、cancel、close。
- ✅ 状态使用 IDLE/LOADING/READY/DEGRADED/ERROR/CLOSING/CLOSED；首次 loading/error 明确 unavailable，degraded 保留已提交 index 查询。
- ✅ 实现 LocalKnowledgeSourceRepository、MarkdownChunker、JsonManifestRepository；路径受限、chunk id 确定、manifest 原子写入。
- ✅ 实现显式注入模型、batch/top-k 和 persist path 的 SentenceTransformerEmbedder/CrossEncoderReranker/ChromaKnowledgeIndex。
- ✅ Settings/bootstrap 显式装配当前路径、模型参数和生命周期；adapter 不读取旧全局 config。
- ✅ KnowledgeService 实现现有 RetrievalPort；ToolDefinition、RuntimeCommand/RuntimeEvent 与 tool closure 不变。

### 4. MemoryService 与一致性

- ✅ 实现 versioned JsonMemoryRepository；一条 Memory 一个新 JSON 文件，不兼容读取旧 Markdown；同时实现 KnowledgeSourceRepository.scan/read，供应用重启或 index 重建时恢复 memories collection。
- ✅ MemoryExtractor 依赖专用 LLMPort、静态 prompt、Clock/IdGenerator 与 operation cancellation，不直接创建旧客户端/loader。
- ✅ MemoryService 显式执行 extract → write → index；只接受 fact/preference，typed parse/extraction failure 不写 repository。
- ✅ repository 写成功而 index 失败保留 manifest observed/indexed 差异；删除使用 delete intent 并支持中断重试。
- ✅ query_memory 继续通过 RetrievalPort 查询 memories collection；MemoryService 不重复实现 search。

### 5. CLI 接入、清理与 G6

- ✅ 通过 `CommandRegistry.replace()` 接入 `/ragreload [target]` 与 `/build-memory`；更新 help/completions，不修改 CliApp 的 Knowledge/Memory 业务分支。
- ✅ 真实 KnowledgeService 与 retrieval contract tests 同一切片替换并删除 DeferredRetrievalAdapter。
- ✅ 补齐 Application 隔离、reload 真正取消、后台 build partial failure、auto-memory、close error/timeout、无全局状态和 25 个工具契约。
- ✅ 使用真实 Chroma/embedder/reranker/reference fixture 完成可复跑 smoke：`uv run python -m scripts.r6_knowledge_smoke` 输出 `R6_SMOKE_OK hits=1 score=0.961208`。
- ✅ G6 重新通过：`uv run python -m unittest discover -s tests/get_me_in -t .` 正常退出，187 项测试通过；`compileall` 通过。

### 6. R6-T 强制终止门禁

- ✅ 已执行 checkpoint，`docs/current.md` 保存为“R6 完成、R7 未启动、等待用户审查”。
- ✅ 已核对本阶段没有创建或修改 R7 文件、类、公开方法，没有切换旧入口，也没有执行 R8 删除。
- ✅ 已向用户提交 R6 代码、测试、真实 adapter smoke、manifest/close 失败路径证据，并停在审查门禁。
- ⛔ 自动进入 R7 设计或 coding —— 必须等待用户后续明确授权。

### 7. R6-F 审查修复（已授权）

- ✅ 切片 1：接通后台启动加载与前台 reload cancellation；分离 Runtime/reload/Memory cancellation；串行保护 search/reload/index/delete。提交：`05c4956`。
- ✅ 切片 2：Chroma replace 先 embedding、失败回滚新 chunk 并保留旧 chunk；删除异常正确传播并保留 manifest retry 状态。提交：`73a1c79`。
- ✅ 切片 3：增加 `BackgroundJobState`、`BackgroundJobResult`、`BackgroundWorker.result(job_id)` 与可取消 task callback；Memory build 返回 typed partial failure。提交：`79c0601`。
- ✅ 切片 3：Memory delete 按 manifest intent → index delete → repository finalize → manifest commit 执行，任一步失败可重试。提交：`79c0601`。
- ✅ 切片 4：worker timeout 时不关闭仍被使用的依赖；Memory/Knowledge 内部 close 失败隔离；修复 composition root 与测试 cleanup 泄漏。提交：`38708e2`。
- ✅ 切片 4：MemoryExtractor 改用静态 prompt；完整自动化测试与 `compileall` 正常结束，真实 Chroma/model smoke 留下可复跑证据。提交：`38708e2`。
- ✅ 重新执行 G6 并通过；再次 checkpoint、停在 R6-T，等待用户审查，不进入 R7。

## R7 —— Resume 纵向切片

> ✅ R7 七个已确认切片、R7-T 与 R7-T2 审查修复均已完成；决策 189 已再次恢复 G7 完成结论。当前停在 R8 独立授权门禁前。

### 0. R7 启动前 Review 门禁

- ✅ 复核 R6-T checkpoint、四个 R6-F 提交和干净工作区；重新运行 187 项核心自动化测试并正常退出。
- ✅ 对照实际代码复核 R7 旧任务：当前生产 composition root 只装配 Main Runtime；Resume 工具仍使用临时 `ResumeArtifactPort`／`LocalResumeArtifacts`，尚无 Artifact schema 或 repository。
- ✅ 用户确认 R7-P dynamic session identity、Resume capability parity 与 agent-scoped Runtime/LLM ownership、独立 Artifact repository、ArtifactService/build-attempt 语义及 typed partial-failure/retry 五项总体边界。
- ✅ 闭合 R7-P：`Orchestrator` 在每次 Runtime transition 传入 `SessionState.session_id`，Runtime 仅在该 transition 内替换 immutable ToolContext scope；restore／rewind 清理真实 session 的 workspace grant，不引入第二份长期 Session 状态。
- ✅ Resume 保留除 `route` 外的 v1 capability parity；Main/Resume 分别拥有 Runtime、CancellationToken、PlanService、ToolContext 和 LLM 生命周期。
- ✅ Artifact 使用全新 `data/runtime/artifacts/` 独立 repository，不写入 Memory、不加入 SessionSnapshot，也不随 rewind 回滚。
- ✅ Artifact operation 采用 pending → side effect → commit；PENDING PDF retry 重新执行构建，不凭同名旧文件合成成功；成功且 PDF 存在才登记可用产物，metadata partial failure 可观察且可重试。
- ✅ 用户确认活跃设计中的 R7 新文件、类、构造依赖、公开方法、允许修改文件和七个实施切片清单。
- ✅ 恢复显式 temperature 契约：Main 为 `0.1`、Resume 为 `0.2`、MemoryExtractor 为 `0.0`；先以独立 R7-P0 切片闭合。
- ✅ Artifact build log 使用固定上限、workspace 根路径脱敏、UTF-8 安全 head/tail 截断，并保存原始字节数和截断标记。

### 1. R7-P0 —— LLM temperature 契约修复

- ✅ `AgentSpec` 增加 `temperature: float`，Main 固定为 `0.1`，Resume 将在其已确认的 AgentSpec 工厂中固定为 `0.2`。
- ✅ `LLMRequest` 增加 `temperature: float | None = None`；MemoryExtractor 请求显式使用 `0.0`。
- ✅ OpenAI adapter 仅在 temperature 非 `None` 时透传，并拒绝非有限值或超出 `[0, 2]` 的配置。
- ✅ 补齐 Main Agent、MemoryExtractor 与 adapter 请求测试；针对性 27 项测试通过。用户已授权自动继续，下一步进入 R7-P。

### 2. R7-P —— 动态 session identity 前置修复

- ✅ 让每次 Runtime 工具执行从当前 `SessionState` 获得 session id，不依赖 bootstrap 时捕获的固定字符串。
- ✅ `restore`／`rewind` 后清除真实当前 session 的 workspace revision grant；连续恢复多个 snapshot 时不得跨 session 复用旧 read authorization。
- ✅ 后续 ArtifactService 将从同一动态 ToolContext 获得 session id 与 `AgentKey.RESUME`，不通过全局变量、CLI 私有状态或可变 session-id 镜像获取 provenance。
- ✅ 补齐双 snapshot 连续 restore、工具 read-before-edit scope 与 main→resume→main handoff context 回归；针对性 29 项测试通过。

### 3. Resume AgentSpec 与 composition root

- ✅ 创建 immutable `build_resume_spec()`，不创建只有元数据方法的 stateful ResumeAgent 类。
- ✅ 按已确认 capability parity 装配 Resume，且不获得 `route`。
- ✅ 保留新建、修改、JD 定制入口与真实经历、重新读取、编译诊断约束。
- ✅ AgentCatalog、SessionState、PlanService 和 Orchestrator 同时装配 Main/Resume；Main 仅通过 descriptor 发现 Resume。
- ✅ Main/Resume Runtime 使用各自的 CancellationToken、PlanService、ToolContext 与不同 LLM；共享 adapter 仍由 ResourceStack 唯一 owner 关闭。
- ✅ 覆盖 capability 隔离、main→resume→main handoff 与取消 scope；完整核心测试 193 项通过。提交：待本 checkpoint 后创建。

### 4. Artifact domain、repository 与 service

- ✅ 定义 `schema_version=1` 的 typed Artifact、build-attempt 与 aggregate ArtifactOperation schema；Artifact 保存 `content_hash` 与 `template_name`，无开放 metadata dict。
- ✅ repository 使用全新 `data/runtime/artifacts/` 边界；路径契约为 workspace-relative，不读取或迁移旧运行数据。
- ✅ 定义 ArtifactRepository 的原子 aggregate 持久化、列举／查询与幂等 close；JSON 语法、顶层／nested schema、字段、枚举、时间与 aggregate 不变量损坏统一返回 typed repository failure。
- ✅ operation key 使用 canonical JSON 的 SHA-256；每条 JSON 记录为 PENDING 或携带结果的 COMMITTED，单次 replace 原子切换。
- ✅ ArtifactService 直接满足 ResumeArtifactPort provenance 契约，并借用 LocalResumeArtifacts backend；保持 LLM 参数 schema 与 ToolOutcome 闭合协议不变。
- ✅ `copy_template` 预检模板、目标 LaTeX、README 与重复后缀；明确 README 覆盖行为，并记录成功文件、来源模板和版本。
- ✅ `build_pdf` 复用现有 ProcessRunner，记录每次成功、非零退出、超时、取消和异常尝试；PENDING retry 重新构建并覆盖旧 PDF，只有实际返回 exit code 0 且目标 PDF 存在时才记录可用产物。
- ✅ build attempt 按配置上限保存 stdout/stderr，脱敏 workspace 根、UTF-8 head/tail 截断并保存原始字节数与标记。
- ✅ 文件副作用后的 Artifact DTO 构造、`content_hash()`、`next_version()` 与 repository commit 均纳入 `ArtifactPartialFailure`；ToolFailure 通过既有 message／suggestion 保留内部 code 与 `changed_paths` 可观察语义。
- ✅ pending operation 只在下一次同 key 调用时惰性恢复；模板复制按内容幂等，PDF 重新构建，不增加 daemon、新 CLI 或 pruning/retention policy。
- ✅ `workspace_open` 已在 R3 通过 Frontend/OS adapter 实现，不由 domain 直接启动 GUI；R7 只做端到端复验。
- ✅ Artifact repository 只保存产物与编译记录；user memory 继续只保存 fact/preference。不把 ArtifactRef 加入 SessionSnapshot，rewind 不删除或回滚工作区文件与 artifact 记录。

### 5. 已确认实施切片

- ✅ 切片 1：R7-P0 temperature contract 与请求透传测试。提交：`dca9d48`。
- ✅ 切片 2：R7-P dynamic session identity 与跨 restore 隔离测试。提交：`2fd3d20`。
- ✅ 切片 3：Resume AgentSpec、capability、双 Runtime composition 与 handoff contract tests。提交：`9839a83`。
- ✅ 切片 4：Artifact domain／port／JSON repository 与 schema/atomicity tests。提交：`bb5b241`。
- ✅ 切片 5：ArtifactService、ResumeArtifactPort 替换、copy/build/log/partial-failure tests。提交：`5893f7a`、`ce805ff`。
- ✅ 切片 6：Settings/bootstrap/resource ownership 接入与跨组件回归。全量 202 项测试与 `compileall` 通过；提交：`96c5dc7`。
- ✅ 切片 7：真实中文／英文／双语 Resume smoke、完整 G7 与 checkpoint。中文、英文、双语共 4 份 PDF 在隔离工作区成功生成；提交：`10941a8`。R7-T 后以 212 项测试和真实 smoke 重新验收。

### 6. 端到端验证

- ✅ 验证 Main、Resume 与 MemoryExtractor 的 temperature 分别为 `0.1`、`0.2`、`0.0`，且 adapter 不覆盖未指定值。
- ✅ 中文模板新建 → 读取 README → 填充 → 编译 → 预览。
- ✅ 英文模板新建 → 读取 README → 填充 → 编译 → 预览。
- ✅ 双语模板复制、文件名防重复后缀和既有目标拒绝覆盖。
- ✅ 修改已有简历与精确 edit/replace；授权清理后旧 revision 被拒绝，重新读取后可编辑并真实编译 PDF。Windows CRLF round-trip 已修复并回归。
- ✅ 外部简历/JD 读取、Memory/Reference 检索和可选 Web Search 的 capability 与 Resume prompt 可见性符合确认清单。
- ✅ pdflatex 缺失、非零退出、超时、取消、编译失败修复、build log 脱敏／截断与完整 metadata partial failure 均有自动化覆盖；真实 smoke 覆盖成功编译。
- ✅ 审批拒绝、Esc cancel、save/restore/rewind、main → resume → main 闭环均通过分层与 production composition 回归。
- ✅ 决策 189 已在 R7-T2 后再次恢复 G7 完成结论；未经用户后续确认不得进入 R8 入口切换或遗留删除。

### 7. R7-T 审查修复（已完成）

- ✅ 完成 R7 代码审查与当前环境复验：205 项自动化测试、`compileall`、`git diff --check` 通过；工作区干净，旧 `main.py` 未改动。本轮未重新执行真实 `pdflatex` smoke。
- ✅ 修复 PENDING build 的旧 PDF 误判：PENDING retry 重新执行受取消／超时控制的构建，不再仅凭同名 PDF 存在合成 `exit_code=0`。提交：`c1fe9dc`。
- ✅ 完整闭合文件副作用后的 typed partial failure：覆盖 Artifact DTO 构造、`content_hash()`、`next_version()` 与 repository commit，并让 ToolFailure 保留 changed paths 的可观察语义。提交：`7a621bd`。
- ✅ 让 Artifact JSON 的字段缺失、类型错误、非法枚举、非法时间、nested schema 及 aggregate 不变量失败统一转换为 typed repository failure，并补齐结构损坏测试。提交：`03e2240`。
- ✅ 补齐 production composition 的 temperature、capability/prompt、审批拒绝、handoff、snapshot/rewind/restore 回归；结合既有 workspace、CLI Esc 与 MemoryExtractor 测试闭合 G7 验收矩阵。提交：`b54157b`。
- ✅ 真实已有简历 edit/replace smoke 发现并修复 Windows CRLF 重复转换；`LocalWorkspace.write()` 现在保持输入换行，精确 edit 后真实 PDF 编译通过。提交：`53d9330`。
- ✅ 最终运行 212 项自动化测试、`compileall`、`git diff --check` 全部通过；真实 ArtifactService 在隔离工作区生成中文、英文、双语共 4 份 PDF，并另行完成已有英文简历 replace、授权清理后重新读取、精确 edit 与编译 smoke。
- ✅ 同步 `current.md`、`task.md`、`decision.md` 并由决策 187 恢复 G7；继续停在 R8 独立授权门禁前。

### 8. R7-T2 审查修复（已完成）

- ✅ 当前环境重新运行 212 项自动化测试、`compileall` 与 `git diff --check`，均通过；工作区在审查前保持干净。
- ✅ 最小复现确认 exception retry 不一致：首次 backend exception 被保存为 COMMITTED attempt 后抛出；第二次同 operation key 直接返回 `ProcessResult(exit_code=None)`，`tools/resume.py::_build_pdf()` 会将其包装为 `ToolSuccess`。
- ✅ 最小复现确认 aggregate validation 不完整：`COMMITTED + BUILD_PDF + 无 build_attempt` 可通过 save/load，随后 `ArtifactService.build_pdf()` 重放泄漏非 typed `IndexError`；deterministic operation key、operation-kind result shape 与 nested 字段类型也未形成完整 invariant。
- ✅ 静态审查确认 composition construction cleanup 不完整：`build_application()` 在 ResourceStack 注册前创建 worker／Knowledge／Artifact 等 owner，部分后续构造或 injected LLM validation 失败路径不会统一关闭已创建资源。
- ✅ 修复切片 1：`JsonArtifactRepository` 的 save/load 共用校验已闭合字段类型、deterministic operation key 与 kind/status/result shape；所有损坏记录统一为 `ArtifactRepositoryError`。未改变 schema_version、公开 repository 方法或 operation key 算法。提交：`e963b11`。
- ✅ 修复切片 2：`ArtifactService.build_pdf()` 首次与重放的 backend exception／非结果状态语义已统一；相同 committed attempt 稳定映射为 `build_pdf_failed`，不再漂移为 `ToolSuccess`。未增加 ToolOutcome 字段或公开方法。提交：`e0e2041`。
- ✅ 修复切片 3：`build_application()` 使用临时 construction ownership stack 清理 ResourceStack 交接前后的失败；覆盖 runtime LLM 配置错误、Memory prompt 读取失败与 knowledge start 失败，不新增全局生命周期。提交：`6af22a3`。
- ✅ 最终运行 216 项自动化测试、`compileall` 与 `git diff --check`；真实临时工作区完成中文／英文模板复制与两份 pdflatex 编译，exit code 均为 0，记录 5 个 artifacts 与 2 个 build attempts。
- ✅ 同步 `current.md`、`task.md`、`decision.md` 并由决策 189 恢复 G7；继续停在 R8 独立授权门禁前。

## R8 —— 切换与清理

> 决策 191 已授权并完成 R8-P，决策 192 完成 R8-E，决策 225 完成 R8-O 及用户审查，决策 227 授权的 R8-D 已由提交 `7514af3` 完成并由 `c13d455` checkpoint。决策 230 已确认 R8-G 详细清单，决策 231 已授权本会话从 5.2 开始实施；R8-G 仍不修改生产代码、测试、依赖或数据，也不自动进入 R9。

### 1. R8-P —— 切换准备

- ✅ 确认 R7-T2 已完成且 G6、G7 均有效；切换前工作区干净，旧 `main.py` 未改动。
- ✅ 复核实际 Catalog：2 个 Agent（Main／Resume）、25 个 ToolDefinition、10 个 CLI 命令；分别从 `AgentCatalog`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 取证，并与 capability 文档一致。
- ✅ 验证 `data/reference/`、`data/prompts/`、`data/resume/template/` 可直接作为当前静态输入。
- ✅ 对旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 建立组合证据：静态扫描禁用路径／legacy-only 环境变量、sentinel project root 的 Settings 路径断言；R8-O 继续执行拒绝访问启动／smoke 边界，mtime／hash 前后证据只用于确认未改写。
- ✅ 将 `.env.example` 补齐为 `Settings.from_env()` 的实际变量、默认值与兼容别名；v1-only 变量暂放在“legacy rollback only”段，R8-O 前不得删除。
- ✅ 为当前空的 README 写过渡说明：同时记录旧生产根入口与新架构预览入口、静态资产、新旧运行数据和回退边界；不提前宣称根入口已切换。
- ✅ 运行当前架构→legacy import scan、入口前完整自动化测试、`compileall` 与 `git diff --check`；R8-P 已独立提交 `d91e37c`。

### 2. R8-E —— 根入口切换

- ✅ `main.py` 只 import `src.get_me_in.cli.main.main` 并 `raise SystemExit(main())`；已删除 legacy composition 与 import-time registration。
- ✅ `src/get_me_in/cli/main.py` 已修正过时说明；Settings 错误继续渲染并返回 `2`，composition／CLI 构造或启动的 `Exception` 以不受 `LOG_LEVEL` 高阈值过滤的 file-only 诊断记录完整 traceback、终端仅渲染简短错误并返回 `1`；正常关闭返回 `0`，关闭异常或 `CloseReport.issues` 对用户可见并返回 `1`。不捕获 `KeyboardInterrupt`／`SystemExit`，未新增第二入口或公开 API。
- ✅ `test_import_boundaries.py`、`test_settings.py`、既有 CLI/bootstrap 测试与 `test_cli_main.py` 覆盖根入口只依赖当前包、示例配置一致性、Settings 错误 `2`、启动错误 `1` 且无 traceback、`LOG_LEVEL=ERROR` 文件诊断、正常关闭 `0`、关闭异常隔离与 typed close issue 可见性。
- ✅ 未新增 `[project.scripts]` 或其他生产入口。
- ✅ R8-E 已独立提交 `9fbeabc`；该提交是遗留删除前的明确回退点。

### 3. R8-O —— 强制观察门禁

- ✅ 从 `uv run python main.py` 验证缺少／非法配置时可读错误退出且无 traceback，正常 `/exit` 返回成功退出码。
- ✅ 修复根入口切换后欢迎 banner 丢失的观察期回归：`Renderer.render_welcome()` 在首次输入前只渲染一次固定产品标识与 `/help` 提示；不扩展 `Settings` 或引入新依赖。
- ✅ 确认新架构 `ToolDefinition`／`PromptRenderer` 只保留 `name/description/type/required`，实际生产 system prompt 已丢失旧版 `purpose/use_when/do_not_use_when/expected_output`、参数说明与默认值；该问题不是 Notebook 导出遗漏。
- ✅ 核对 legacy Tool 基线仍在 `src/tools/`：9 个工具定义文件保留上述元数据，当前未被重构修改；逐项迁移审计若发现缺失或历史改写，再由用户提供原始定义。
- ✅ Tool 提示词语义修复清单已确认并实施：`ToolDefinition` 恢复 purpose/use_when/do_not_use_when/expected_output，`ToolSchema` 使用强类型 `ToolParameter` 表达 description/default/items/allowed_values/nullable；PromptRenderer 恢复 legacy `<Tool>` XML 外层与固定语义顺序，`Arguments` 内由强类型 schema 生成有序 JSON；保持当前 capability、审批、handler 与 ToolOutcome 边界。
- ✅ 全部 25 个工具已与 9 个 legacy 定义文件一一对应并完成迁移；`workspace_edit.revision` 等已确认接口差异保留并补充准确说明，没有工具缺失，无需用户另行提供原始定义。
- ✅ 修复 Tool prompt 字段被 `sort_keys=True` 重排为字母顺序的问题；模型固定先看到用途和使用边界，再看到参数及预期输出。恢复 XML 仅影响 LLM-facing 序列化，不恢复 legacy import-time Registry。
- ✅ 相邻 `<Tool>` 块使用 `\n\n` 分隔，在模型可见 prompt 中保留一个空行；回归测试锁定 `</Tool>\n\n<Tool ...>` 格式。
- ✅ 核对 production Catalog 只有 Main／Resume 是既定范围而非迁移遗漏：legacy JobSearchAgent 仅为 M4 测试壳，完整 Job Search 在 R0～R8 冻结，保留 `AgentKey.JOB_SEARCH` 与通用 handoff 测试作为未来扩展点，本次不新增 Agent。
- ✅ SubAgent prompt 恢复 legacy XML 语义结构：`<SubAgent name>` 内固定输出 `Name`、`Description`、`Responsibilities`、`HardConstraints`，多个块以空行分隔；只有具备 Route capability 的 Agent 注入列表，修复 Resume prompt 把 Main 错列为子 Agent 的问题。
- ✅ SubAgent 修复的 30 项 Prompt/bootstrap/Catalog/orchestration 回归、完整 235 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 production composition 输出 `SUBAGENT_XML_SMOKE_OK main_chars=11930 resume_chars=19809 agents=2 tools=25`，确认 Main 只见 Resume、Resume 不见任何 SubAgent、JobSearch 未被误装配。
- ✅ 确认 CommunicationStyle 同样存在真实迁移缺失而非导出问题：Main／Resume 的 Tone、Verbosity、ExplanationStyle 被概括改写，StyleRules／StyleAvoids 全部为空；legacy 原始定义仍完整保留。
- ✅ 将 Main／Resume 五类 CommunicationStyle 元数据逐项恢复到 immutable `AgentStyle`；不修改 `06_communtion_style.md`、PromptRenderer 接口或运行时协议，完整对象相等测试锁定所有规则与避免项。
- ✅ CommunicationStyle 修复的 26 项 bootstrap/Prompt/Catalog 回归、完整 236 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `COMMUNICATION_STYLE_SMOKE_OK main_chars=12111 resume_chars=20104 agents=2 tools=25`，确认五个区块均非空且包含原始中文内容。
- ✅ 排除 Tool、SubAgent、InputFormat、OutputFormat 后继续审计完整 system prompt：静态模板、Role／Constraints 的固定 Must、Reserved 与已修复 CommunicationStyle 均无差异；剩余差异全部来自 Main／Resume `AgentSpec` 中 Role、Mission、Constraints 动态元数据被大幅压缩和改写。
- ✅ Main 的 Name、Description、7 条 Responsibilities、PrimaryGoal、5 条 SuccessCriteria、5 条 Priorities、10 条 HardConstraints、4 条 SoftConstraints 按 legacy 原始语义和列表前缀恢复；过时的 `switch_agent` 标识符适配为当前真实工具名 `switch_to_subagent`。
- ✅ Resume 的 Name、Description、5 条 Responsibilities、PrimaryGoal、4 条 SuccessCriteria、5 条 Priorities、7 条 legacy HardConstraints、4 条 SoftConstraints 恢复；额外保留“不得编造/夸大经历”和“不得调度其他子 Agent”两项强化硬约束，共 9 条。
- ✅ Agent metadata 修复的 32 项 bootstrap/Prompt/Catalog/orchestration 回归、完整 237 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `AGENT_METADATA_SMOKE_OK main_chars=13159 resume_chars=20806 agents=2 tools=25`，确认恢复内容实际进入 Main／Resume system prompt，且未重新引入旧 `switch_agent` 标识符。
- ✅ 定位偶发 model reply warning：模型返回了 InputFormat 风格的完整历史消息 envelope，在 `event_type=finish` 时遗漏 OutputFormat 必填的字符串 `thinking`；一次格式修复虽能恢复，但增加模型调用和延迟。
- ✅ 模型输出协议收敛为 `event_type/message/thinking/tool/event_payload` 五类业务字段；`id/role/timestamp/tool_call_id/plan_status` 明确由 Runtime 生成。解析器移除 `content + nested tool_call` 隐式兼容，按事件类型严格验证必需业务字段、类型和 finish/tool_call 条件组合。
- ✅ 决策 201 曾将 `07_output_format.md` 显式置于完整 system prompt 最后；该硬编码重排已由决策 213 撤销，当前改由 `07_input_format.md`、`08_output_format.md` 文件名表达顺序，PromptRenderer 严格按文件名排序拼接。
- ✅ PromptRenderer／Runtime／bootstrap 定向 47 项和完整 264 项测试通过；production 模板回归锁定九个 XML 区块与数字文件名顺序一致，legacy PromptLoader 可按新名称读取 OutputFormat。
- ✅ 修正 conversation tool-call correlation：tool_call 历史使用 `id=event_id`、`tool_call_id=call_id`，对应 tool result 复用相同 `tool_call_id`；Runtime 生成的 record 保存当时 Plan 快照，ConversationCodec 投影 `{current, completed, remaining}`，SessionSnapshotCodec 对缺失 record plan 保持向后兼容。
- ✅ 用户复审后将多余字段策略改为允许列表投影：`id/role/timestamp/tool_call_id/plan_status` 和任意未知顶层字段均直接忽略，Runtime 重新生成可信内部值，不为可安全丢弃的信息消耗 repair 调用；业务字段错误仍沿用一次修复边界。
- ✅ 调整后的 62 项 Parser/Prompt/Conversation/Session/Runtime/bootstrap 定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `OUTPUT_PROJECTION_SMOKE_OK chars=12825 tools=25`，确认末尾 OutputFormat 与忽略／重建规则可见。
- ✅ 定位工具结果后偶发纯文本回复：09:39:42 Resume call 3 完全未输出 JSON，Runtime 正确 repair 并在 call 4 恢复，但增加一次 provider 调用和约 45 秒延迟；新架构 OpenAILLMAdapter 相比 legacy 丢失 `response_format={"type":"json_object"}` 是直接回归。
- ✅ OpenAILLMAdapter 对所有 completion 恢复 provider JSON object mode；当前调用方只有要求 JSON 对象的 AgentRuntime 与 MemoryExtractor，OpenAIWebSearchAdapter 保持独立协议。保留 Prompt OutputFormat、内部 Parser 和一次 repair 三层边界。
- ✅ provider JSON mode 的 49 项 OpenAI adapter/Runtime/Memory/bootstrap 定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 Pro 模型输出 `PROVIDER_JSON_MODE_SMOKE_OK keys=['ok']`，确认当前 provider 接受 json_object 并返回可解析对象。
- ✅ 确认新架构 ModelReplyParser 曾只使用 `json.loads`，`json-repair` 虽仍在依赖中但仅被 legacy `src/message.py` 使用；任何 JSON 语法错误都会触发额外模型调用，属于迁移遗漏。
- ✅ 新架构在既有模型修复前增加本地 JSON 语法修复：标准 `json.loads` 失败后调用 `json_repair.loads`；尾逗号、物理换行等修复结果仍须为 object 并继续完整业务校验，成功时不增加模型调用。
- ✅ 保持严格输出契约：纯文本、JSON string／array、缺少 finish message、错误业务字段类型或 finish/tool 冲突均不得归一化；finish thinking 可省略但若提供必须是 string。本地 repair 失败或语义校验失败时，AgentRuntime 注入具体错误与 canonical OutputFormat 并只允许模型自修一次，第二次仍失败返回 `invalid_model_reply`。`repair_attempted` 继续承担运行时重试边界和 snapshot 持久化职责。
- ✅ 本地 repair／单次模型自修边界的 61 项 Parser/Runtime/provider/bootstrap/snapshot 定向测试与完整 244 项自动化测试通过；`compileall` 与 `git diff --check` 通过。
- ✅ R8-O 真实 Main 回复发现 `finish.thinking=""` 会合法通过且不显示摘要；决策 212 曾将 finish thinking 收紧为非空，现由决策 219 推翻，恢复 finish thinking 可省略或为空字符串的语义，tool_call thinking 规则不变。完整自动化测试、`compileall` 与 `git diff --check` 通过。
- ✅ 真实 Main 对话发现能力宣传漂移：问候声称可准备面试、推荐学习资料，但 production Catalog 当前只有 Resume SubAgent；Java 学习资料无匹配项时仍给出 Coursera／Udemy／Stack Overflow 等替代建议。
- ✅ 用户确认 Main 工具白名单：全部 Plan 工具、`get_current_datetime`、`provide_choices`、`read_customer_file`、`query_memory`、`switch_to_subagent`；其余工具全部不可见。上述工具仅用于意图识别、上下文收集与路由，不构成用户可见业务能力。
- ✅ 用户确认 `<SubAgents>` 是 Main 当前业务能力的唯一且穷尽来源；不得根据产品名称、工具、历史消息、模型知识或未来规划推测、宣传或执行列表外能力。无匹配 SubAgent 时只说明当前不支持，不提供替代建议；问候可按实际列表介绍能力，但不得暴露 Agent／工具／路由内部结构。
- ✅ 细分 capability：新增 `CURRENT_DATETIME` 与 `MEMORY_QUERY`；`get_working_dir` 改由 `WORKSPACE_READ` 控制，`query_reference_data` 继续由 `KNOWLEDGE_QUERY` 控制。Main 移除 `SYSTEM`、`WEB_SEARCH`、`KNOWLEDGE_QUERY`，精确保留四个 Plan 工具、`get_current_datetime`、`provide_choices`、`read_customer_file`、`query_memory`、`switch_to_subagent`；Resume 保持其既有领域能力。
- ✅ 强化 `01_role.md`、`04_tools.md`、`05_sub_agents.md` 与 Main `AgentSpec`，明确用户请求不能授权越权、辅助工具不等于业务能力、SubAgent 列表权威且穷尽、禁止能力推测、无匹配项不得替代回答，以及问候只能介绍当前真实能力。同步移除 `query_memory`／`read_customer_file` 对不可见工具的名称泄漏，修正 Resume “其他能力退回 Main 处理”的错误暗示。
- ✅ production composition 回归锁定 Main 精确 9 工具集合、Resume 既有工具不回退、Main 只见 Resume、提示词权威规则可见且 Main prompt 不再出现学习／面试能力暗示。49 项定向测试、完整 244 项自动化测试、`compileall` 与 `git diff --check` 通过。
- ✅ 真实 `uv run python main.py` 对话 smoke：问候只介绍简历定制／优化；Java 学习资料请求只说明当前不支持，没有推荐平台、资料或替代方案；`/exit` 返回退出码 0。
- ✅ 真实 production composition 的 Main／Resume system prompt smoke 通过：Catalog 仍为 25 个 Tool，完整元数据、参数约束、XML 语义顺序、Tool 块空行和 capability 隔离均可见；最新输出为 `PROMPT_XML_SPACING_SMOKE_OK main_chars=11733 resume_chars=19880 tools=25`。相关 23 项回归、完整 234 项自动化测试、`compileall` 与 `git diff --check` 通过。
- ✅ 修复空 Memory collection 查询语义：`ChromaKnowledgeIndex.search()` 仅将明确的 collection-not-found 归一化为空结果；连接、查询、embedding、rerank 等其他异常继续上抛并由 Tool 映射为 typed `retrieval_unavailable`。
- ✅ 增加 adapter 与 retrieval Tool 回归，覆盖未创建 `memories` collection 时返回零命中，以及非 collection-not-found 异常不得被吞掉。
- ✅ 在真实 Memory smoke 前执行一次性受控迁移：把当前 `data/memories/resume/` 下两份 legacy Markdown 记忆转换为 2 条 `MemoryRecord` JSON 并通过既有 KnowledgeService 建立 `memories` 索引；原文件 hash／mtime／长度不变，production 未增加 legacy 路径扫描或常驻兼容层。
- ✅ 迁移后验证当前 repository、manifest、Chroma `memories` collection 与 `query_memory` 的真实命中；smoke 另发现 targeted reload 会误删非目标 manifest entries，已恢复 reference 索引并将 diff 限制到同一 target 范围，同时回归目标范围内真实缺失仍会删除。最终真实 `/ragreload memories` 只报告两条 memory unchanged；Chroma 为 `memories=36`、`references=34` chunks，manifest 为 2 条 memory 与 6 条 reference source，全部 `ready`。30 项定向测试、完整 249 项自动化测试、`compileall` 与 `git diff --check` 通过。
- ✅ 修复 RAG 后台加载语义：`KnowledgeIndexPort` 增加最小 `prepare(cancellation)`；startup reload 在 manifest diff 前幂等预热 embedding 与 reranker，只有模型和索引均就绪才进入 `READY/DEGRADED`。manifest 无变化仍预热，失败保持 `ERROR` 且显式 reload 可重试，首次用户查询不再承担模型构造。
- ✅ 恢复生产 CLI 权重加载静默配置：在 build application 前固定设置 `HF_HUB_DISABLE_PROGRESS_BARS=1`、`TQDM_DISABLE=1`、`TRANSFORMERS_VERBOSITY=error`，并将 Hugging Face／transformers／sentence-transformers logger 限制为 ERROR；继续保留 encode／predict 的 `show_progress_bar=False`。
- ✅ 后台预热修复的 41 项 Knowledge/Adapter/Retrieval/CLI 定向测试、完整 253 项自动化测试、`compileall` 与 `git diff --check` 通过。真实 `uv run python main.py` 在欢迎界面出现后后台等待 20 秒，终端无权重／进度输出；首次 `query_memory` 约 2 秒完成真实命中且无延迟加载输出，`/exit` 返回 0。
- ✅ 修复 selection Ctrl+C 错误退出 SubAgent：新增 typed `CancelSelection(request_id, reason)`，只把 cancelled result 写回 `provide_choices` 并继续当前 Agent；CliApp 不再把 selection 的 `None` 映射为全局 `Cancel`。Esc／运行取消产生 `Cancelled` 但保留活动 SubAgent handoff，业务失败仍按既有规则关闭 handoff。
- ✅ selection 局部取消改为 `Paused/WAITING_FOR_USER`：取消结果写入历史并回到 CLI，下一条用户消息再继续当前 Agent；Runtime/CLI/Orchestrator 定向测试 46 项通过，`git diff --check` 通过。全量测试复跑时仅出现既有 KnowledgeService 锁释放时序波动，相关单测单独重跑通过。
- ✅ 按用户提供的 legacy 定义新增 Resume-only `merge_pdfs`：保留 first → second 顺序与可选 `.pdf` 后缀，使用既有 capability/审批/ToolOutcome 边界；Main 不可见。
- ✅ PDF 合并经 `ResumeArtifactPort → ArtifactService → LocalResumeArtifacts` 实现；不扩展文本型 `WorkspacePort.read()`，适配器只在 `workspace.resolve()` 约束后用 `pypdf` 读取，并通过同目录临时文件原子替换输出。拒绝相同输入及输出覆盖源文件。
- ✅ Artifact operation 增加 `MERGE_PDFS`，输入使用两个源 PDF 的原始字节 hash，输出 Artifact 记录 hash/version/page count；COMMITTED replay 不重复写入，metadata commit 失败返回 typed partial failure。项目显式依赖 `pypdf>=6.0.0`，锁定 6.14.2。
- ✅ `merge_pdfs` 的 58 项定向测试与完整 261 项自动化测试通过；真实三页 PDF 顺序 smoke 由不同页面尺寸验证 first → second 顺序。`compileall`、`git diff --check` 与 import boundary 复验通过。
- ✅ 将 uv 默认 PyPI 镜像从 SJTUG 切换为唯一的清华 TUNA index，不增加 `[tool.uv].environments`、官方 PyPI、第二个普通镜像或 PyTorch 专用源；保持 Windows／Ubuntu/Linux universal lock。执行前确认无并发 `uv lock`／`uv add`，普通 `uv lock` 与 `uv sync --locked` 均完成。
- ✅ 锁文件前后均为 133 个包且 name/version 集合完全一致；无官方 PyPI 或 SJTUG 残留。记录后续依赖工作流为 `uv add <package> --no-sync` → `uv sync`，分别诊断解析和下载／安装耗时；TUNA 同步后 58 项 PDF 定向测试、完整 261 项测试与 `compileall` 通过。
- ✅ 完成基础对话、`/help`、`/edit`、`/approval`、`/dump`、`/restore`、`/rewind`、`/ragreload`、`/build-memory`、`/exit_sub`、Esc cancel 与关闭 smoke；用户确认完整人工 CLI／交互 matrix 无问题。
- ✅ 完成 Main→Resume→Main、审批拒绝、Plan、Knowledge/Memory query/build/delete 与真实 Resume copy/read/edit/replace/build/open smoke；工程侧真实 Memory delete 验证删除前命中 1 条、删除后命中 0 条。
- ✅ 执行拒绝访问旧目录的启动／smoke 边界并完成目录 mtime／hash 人工检查：4 个 legacy 目录设置为访问即失败后，隔离 production composition 完成 Knowledge 启动和一轮 Runtime；确认当前运行只写显式 `data/workspace/` 与 `data/runtime/`。
- ✅ 重新运行完整自动化测试、`compileall`、`git diff --check` 和 import scan；全量测试发现的 KnowledgeService 状态读取／锁释放竞态由提交 `9da3242` 修复，随后 20 项定向测试与完整 283 项测试稳定通过，Catalog 为 2 Agent／26 Tool／10 command。
- ✅ 用户审查 R8-O；用户确认完整人工 smoke matrix 无问题，工程验证全部通过。R8-O 完成；后续决策 227 已单独授权新会话执行 R8-D。

### 4. R8-D —— 遗留删除（已授权，新会话执行）

#### 4.1 清单分析与授权门禁

- ✅ 按当前 `HEAD` 复核 Git 跟踪的删除白名单：8 个 legacy production package（`src/agents/` 8 个文件、`src/cli/` 4 个、`src/llm/` 2 个、`src/memory/` 6 个、`src/prompts/` 2 个、`src/rag/` 5 个、`src/tools/` 11 个、`src/utils/` 7 个）和 6 个顶层 legacy module，共 51 个跟踪文件。
- ✅ 复核本地 checkpoint 白名单：`.ipynb_checkpoints/`、`src/.ipynb_checkpoints/`、`src/llm/.ipynb_checkpoints/` 均被 Git 忽略，当前共包含 5 个文件；未发现 reparse link。它们只能作为单独的本地清理项处理。
- ✅ 初查 `pyproject.toml` 的 11 个直接依赖均仍被 `src/get_me_in/` 使用，包括延迟导入的 `pdfplumber`、`python-docx`、`chromadb` 与 `sentence-transformers`；当前没有依赖删除候选，R8-D 执行后仍须复核，若证据不变则保持 `pyproject.toml`／`uv.lock` 原样。
- ✅ 确认临时 `scripts/v2_runtime_smoke.py` 已随 R5 正式 CLI 落地删除；现存 `scripts/r6_knowledge_smoke.py` 不属于 R8-D 删除白名单。
- ✅ 用户已审查本节完整清单并明确授权在新会话执行 R8-D；本次文档收敛会话不执行删除，新会话从 4.2 开始。

#### 4.2 删除前安全快照

- ✅ 确认工作区无未提交修改，并记录 R8-D 的父提交；确认 R8-E 回退提交仍为 `9fbeabc`，R8-O 修复与 checkpoint 均已包含在当前历史中。
- ✅ 重新生成 51 个 Git 跟踪文件的精确清单，并检查白名单目录中的非跟踪／忽略内容、symlink／reparse point；如出现除生成型 `__pycache__`／`.pyc` 与已知 checkpoint 外的意外内容，立即停止并重新审查，不按目录整体删除。
- ✅ 对 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 记录删除前只读指纹／mtime 基线，并确认本轮所有待执行命令都不以 `data/`、工作区根目录、通配符或未解析变量作为删除目标。
- ✅ 再次确认保留白名单：`src/__init__.py`、完整 `src/get_me_in/`、`tests/get_me_in/`、`data/reference/`、`data/prompts/`、`data/resume/template/`、`data/workspace/` 与 `data/runtime/`；R8-D 不迁移、覆盖或删除任何旧 `data/` 运行数据。

#### 4.3 精确删除

- ✅ 仅按精确路径删除 `src/agents/`、`src/cli/`、`src/llm/`、`src/memory/`、`src/prompts/`、`src/rag/`、`src/tools/`、`src/utils/` 中已复核的 45 个 Git 跟踪文件及目录内生成型缓存。
- ✅ 仅按精确路径删除 `src/config.py`、`src/lifecycle.py`、`src/logger.py`、`src/message.py`、`src/request.py`、`src/response.py`。
- ✅ 单独解析并核对三个 checkpoint 目录仍位于仓库内，再以 literal path 删除 `.ipynb_checkpoints/`、`src/.ipynb_checkpoints/`、`src/llm/.ipynb_checkpoints/`；禁止使用 `git clean`、宽泛递归搜索或通配符清理。
- ✅ 删除后逐项断言 8 个 legacy package、6 个顶层 legacy module 和 3 个 checkpoint 目录均不存在，同时断言全部保留白名单仍存在。
- ✅ 审查 `git diff --name-status`：除已确认的 51 个 legacy 源文件删除外不得出现其他 tracked 变更；不得出现 `data/`、`src/get_me_in/`、`tests/get_me_in/`、`main.py`、文档或配置文件改动。

#### 4.4 删除后验证

- ✅ 再次扫描 `main.py`、`src/get_me_in/`、`tests/get_me_in/` 与生产配置，确认没有 legacy import、动态 import 字符串、旧模块路径或 import-time registration 依赖；`test_import_boundaries.py` 的 forbidden module 清单继续作为防回归规则保留。
- ✅ 复核 11 个直接依赖的当前使用证据；若仍全部使用，保持 `pyproject.toml`／`uv.lock` 不变。若出现新的未使用证据，停止 R8-D，不在删除提交中顺带猜测性移除依赖。
- ✅ 运行 `uv run python -m unittest discover -s tests/get_me_in -t .`、`uv run python -m compileall src/get_me_in main.py` 与 `git diff --check`；任何失败先定位并恢复绿灯，不得以删除 legacy 测试或放宽契约解决。
- ✅ 从实际 Catalog 复核 2 个 Agent、26 个 ToolDefinition、10 个 CLI 命令，并执行根入口启动／`/exit`、production composition 及拒绝访问 4 个 legacy data 目录的删除敏感 smoke；R8-G 再执行完整真实 adapter 与业务 smoke matrix。
- ✅ 比较 4 个旧运行数据目录的删除前后指纹／mtime，并确认没有读取、改写、迁移或删除；“未读取”仍以静态扫描、Settings sentinel 与拒绝访问 smoke 为主证据。

#### 4.5 提交与回退

- ✅ 仅暂存 51 个 legacy 源文件删除，复核 staged diff 后创建独立 R8-D 提交 `7514af3`；checkpoint 本地清理不伪装为 Git 变更，R8-G 文档归一化不得混入该提交。
- ✅ 提交后确认工作区干净、R8-D 提交可单独 revert，随后才进入 R8-G；R8-G 完成前仍保留 `.env.example`／README 的 `legacy rollback only` 说明。
- ✅ 记录并复核紧急回退顺序：R8-D 前只需 `git revert 9fbeabc`；R8-D 后先 revert R8-D 恢复 legacy 源码，再 revert `9fbeabc` 恢复旧入口。恢复源码后才允许重新启用 legacy-only 配置，任何回退都禁止触碰旧运行数据。

### 5. R8-G —— 文档归一化与 G8（已完成并通过最终审查）

#### 5.1 清单确认与实施门禁

- ✅ 在 R8-D 前按用户要求将活跃重构内容收敛到 `docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/decision.md`，删除并行的 `docs/refactor-design.md`、`docs/refactor-plan.md`、`docs/refactor-task.md`；历史 v1 内容由 Git 保留。
- ✅ 将 capability parity、G0 audit、legacy CLI smoke、legacy entry baseline 与当前 static asset boundary 的有效内容映射到四份主文档和 Git 历史，并删除五份辅助文档；`docs/` 只保留 `current.md` 与四份主文档。
- ✅ 用户审查 R8-D 完成情况：提交 `7514af3` 仅删除 51 个白名单文件，`c13d455` 完成 checkpoint；本轮独立复验 283 项 unittest、`compileall`、`git diff --check` 与生产 legacy import／动态 import 扫描均通过。
- ✅ 用户接受本节 5.1～5.6 的详细清单，并明确本会话只更新文档、不修改代码；本项只确认清单，不构成 R8-G 实施授权。
- ✅ 新会话已执行 `/project-bootstrap`，确认工作区干净、`HEAD` 包含 `c13d455` 与 `7514af3`，并取得用户对 R8-G 的单独明确授权；现从 5.2 开始。
- ✅ R8-G 只允许修改 `.env.example`、`README.md`、`AGENTS.md`、`docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md` 与 `docs/decision.md`；不得修改 `main.py`、`src/`、`tests/`、`scripts/`、`data/`、`pyproject.toml` 或 `uv.lock`。
- ✅ 已确认：若 G8 暴露生产代码、测试、依赖、公开协议或数据迁移缺陷，立即停止 R8-G，保留失败证据并提交独立修复清单供用户审查；不得把修复混入 R8-G 文档／配置提交，也不得以改测试、放宽契约或跳过真实 adapter 获得绿灯。

#### 5.2 过渡配置与 README 归一化

- ✅ 删除 `.env.example` 顶部的 R8 观察期说明和 `legacy rollback only` 段；保留所有正式变量，以及仍支持的 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE` 兼容别名说明。
- ✅ 将 `.env.example` 与实际 `Settings.from_env()` 逐项核对：变量名、必填项、默认值、类型、目录边界和兼容别名一致；未增加或删除 Settings 字段；示例配置解析验证通过。
- ✅ 将 README 从“受控迁移／R8-O 观察期”改为当前基线事实，记录唯一生产入口、诊断模块入口、Main／Resume 当前能力、10 个 CLI 命令、环境配置入口、静态输入、当前运行目录、旧数据保留边界和紧急回退顺序。
- ✅ README 未把历史 `/auto-approve-switch`、25-tool baseline、JobSearchAgent 或 R9 备忘写成当前能力；Catalog／Registry 数量来源已注明为实际代码导出。

#### 5.3 活跃文档与 AGENTS.md 归一化

- ✅ 本 checkpoint 已把 AGENTS.md 从 R8-D 删除执行说明切换为 R8-G 新会话恢复、变更白名单、G8 验证与失败分流说明；R8-D 的精确删除清单继续由 Git、任务历史与决策 226／229 保存。
- ✅ 前一 checkpoint 已将 `docs/current.md`、本任务清单、`docs/design.md` 与 `docs/plan.md` 的当前态收敛到 R8-D 完成与 R8-G 待授权事实，并追加决策 230；该状态在实施期由决策 231 更新为 R8-G 实施中，现已由决策 240 收口为 R8 完成。
- ✅ R8-G 5.3 checkpoint 当时把 `docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/current.md` 与 AGENTS.md 同步为 R8-G 实施中和 G8 待验收；最终审查已将这些活跃入口统一为 R8 完成并停在 R9 授权门禁前，历史阶段证据未被抹除。
- ✅ `docs/decision.md` 保持 append-only：未改写决策 225～230 的历史语义；本 checkpoint 只追加决策 233。
- ✅ 已运行过渡态文本扫描；当前态不再声称 legacy 源码仍存在、R8-O 尚未通过、R8-D 尚待执行或只需单独回退 R8-E，历史章节保留时均按历史阶段理解。

#### 5.4 G8 自动化、静态与 Catalog 验证

- ✅ 独立修复 `tests/get_me_in/test_settings.py` 的过渡配置断言，提交 `ee558b4`；针对性 Settings 测试 12/12 通过。随后完整 unittest 运行 283 项并通过，只有已记录的 Chroma telemetry deprecation warning 与预期错误路径日志。
- ✅ 扫描 `main.py`、`src/get_me_in/`、`tests/get_me_in/` 和生产配置：生产路径无 legacy import、动态 import 字符串、旧模块路径或 import-time registration；测试中的旧模块字符串仅位于 forbidden-module 防回归清单。51 个 legacy production modules 与 3 个 checkpoint 目录不存在，静态输入和保留路径完整。
- ✅ 从实际 `AgentCatalog.list_descriptors()`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 复核 2 个 Agent（Main／Resume）、26 个 ToolDefinition 与 10 个 CLI 命令；取证输出为 `CATALOG_OK 2 ['main', 'resume'] 26 10`。
- ✅ 核对 `.env.example`、README、AGENTS.md 和活跃文档中的入口、配置、Agent、Tool、命令与数据目录描述；`compileall` 与 `git diff --check` 通过；并修正 `docs/decision.md` 230～234 的章节嵌套和目录顺序，未改写历史决策正文。

#### 5.5 G8 根入口、真实 adapter 与数据边界 smoke

- ✅ 根入口 PTY 复核欢迎界面、`/help`、`/approval auto`／切回 prompt、`/dump`、`/restore`、`/rewind` 无候选、`/ragreload`／`/build-memory` 调度、无 handoff 时的 `/exit_sub false` typed 错误与 `/exit`；进程正常退出，历史人工 smoke 已覆盖基础对话、handoff、审批拒绝、Esc／选择取消、restore／rewind 与资源关闭。
- ✅ 真实 KnowledgeService 使用 Chroma／embedder／reranker 完成 prepare、reload、query、source delete 与 close，输出 `KNOWLEDGE_RELOAD_SMOKE_OK added=1 hits=1 deleted=1 after=0 state=ready`；真实 MemoryService 使用当前 JSON repository、MemoryExtractor 与后台 worker 完成 build／query／delete，输出 `MEMORY_SMOKE_OK job=memory-build-1 records=1 hits_before=1 hits_after=0`。
- ✅ 独立修复 `src/get_me_in/adapters/subprocess_runner.py` 的确定性 UTF-8 输出解码与替换策略，并在 `tests/get_me_in/test_subprocess_runner.py` 增加非法输出／`None` 回归断言；提交 `6a092b5`。针对性测试 4/4、完整 unittest 284/284、`compileall` 与 `git diff --check` 通过；此前 `UnicodeDecodeError`／`stdout=None` 阻塞已解除。
- ✅ 已完成中文、英文、双语 Resume copy／read／edit／replace／build／open 的真实链路复验，以及 `merge_pdfs` 的 first→second 页面合并、Artifact metadata 与幂等 replay；本次实际合并 PDF 为 4 页，构建退出码均为 0，未出现 `None`。
- ✅ 对 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 完成静态 forbidden-path／legacy-env 扫描、`SETTINGS_SENTINEL_OK` 与既有拒绝访问 smoke／只读 metadata 证据；未迁移、覆盖、删除或打开旧用户文件内容。
- ✅ 确认 production 只复用 `data/reference/`、`data/prompts/`、`data/resume/template/`，运行写入仅落在 `data/workspace/`、`data/runtime/` 与诊断日志目录；本轮真实 worker、模型 adapter、Knowledge／Memory／Artifact 资源均显式 close，根入口进程正常退出。

#### 5.6 提交、回退与停止门禁

- ✅ 复核 `git diff --name-status ecb11db..HEAD`：R8-G 文档／配置变更只涉及 8 个白名单文件；独立授权的 `6a092b5` 与 `ee558b4` 代码／测试修复保持为独立提交，未混入文档 checkpoint；最终工作区干净，`git diff --check` 通过。
- ✅ 完成 G8 全量证据汇总并建立独立 checkpoint 链：5.2 `c644b12`、5.3 `7e400bd`、5.4 `7742d85`、5.5 `8bd8759`；代码缺陷修复 `6a092b5` 单独提交，R8-G 文档／配置变更未扩大生产边界。
- ✅ 记录两种紧急回退：当前 R8-D 后、R8-G 前按 `git revert 7514af3` → `git revert 9fbeabc`；R8-G 提交后按逆提交顺序先 revert R8-G 文档提交，再 revert `7514af3`，最后 revert `9fbeabc`。只有 legacy 源码恢复后才允许实际启用 legacy-only 配置，任何回退都不得触碰旧运行数据。
- ✅ G8 与 checkpoint 已完成；当前停止等待用户审查，不自动进入 R9。
- ✅ 最终用户审查确认 R8 工程任务与 G8 证据完成，并授权修正活跃文档状态漂移；AGENTS.md、design、plan、task、current 已统一为 R8 完成，决策 240 记录收口，当前停在 R9 独立授权门禁前。

## R8-F —— 模型输出协议稳定性修复（R8 后续，独立于 R9）

### 1. 研究、决策与新会话门禁

- ✅ 对照当前 `FinishFormat`／`ToolCallFormat`、`ModelReplyParser`、Runtime repair 状态与重构前单一 schema，确认格式分支和严格条件组合扩大了模型输出错误面。
- ✅ 最小复现确认：同一用户 turn 内首次格式 repair 成功并继续工具调用后，后续格式错误因 `repair_attempted=True` 直接进入 `Paused("invalid_model_reply")`。
- ✅ 用户确认改为唯一 `message/thinking/tool_call` envelope，Parser 继续只返回现有 `ModelReply`，不改变 RuntimeEvent／Session 消息／工具／handoff／CLI 协议。
- ✅ 用户要求提高每回合 repair 冗余；计划固定为每个 Agent 用户 turn 最多 3 次模型格式修复，本地 `json_repair` 不计数，第四次失败暂停，下一条 `UserMessage` 清零。
- ✅ 用户确认必须增加自动化回归；真实模型随机性由用户在工程验证后执行最终 smoke。本会话只更新文档，不修改生产代码或测试。
- ✅ 新会话已执行 `/project-bootstrap`，确认工作区干净、`HEAD` 包含决策 242 文档提交；只实施本节清单，不检查或进入 R9。

### 2. 单一 OutputFormat 与 Parser

- ✅ 将 `data/prompts/general_agent/08_output_format.md` 收敛为一个固定 JSON envelope：`message`、可选／nullable `thinking`、nullable `tool_call`；`tool_call=null` 为 finish，object 为工具调用。
- ✅ 删除模型输出中的 `event_type`、顶层 `tool`、`event_payload` 要求；保留 Input／Output 区分、单对象／无 Markdown、物理换行转义和 Runtime 内部字段重建说明。
- ✅ 更新 `ModelReplyParser`：只解析新 envelope；finish message 必须非空；tool_call 必须含非空 name，arguments 缺失／null 归一化为 `{}`；未知顶层字段忽略；纯文本、array、JSON string、非法 tool_call 和非字符串字段继续拒绝。
- ✅ 不恢复 `event_type/message/tool/event_payload` 或 `content + nested tool_call` 的双协议兼容；原始模型回复不进入 snapshot，切换无需会话数据迁移。
- ✅ 更新 `test_model_reply.py` 与既有 Prompt 定向覆盖，覆盖唯一 schema、finish、tool call、thinking／arguments 宽容边界、非法语义组合、未知字段投影、本地 JSON repair 与旧 flat 形状拒绝；19 项定向测试通过。

### 3. 三次 repair 预算与 snapshot 兼容

- ✅ 将 `AgentSessionState.repair_attempted: bool` 替换为 `format_repairs_used: int = 0`；未保留第二份 domain canonical repair 状态。
- ✅ Runtime 每安排一次模型格式 repair 将计数加一；同一 turn 的合法解析与工具执行不清零，最多允许 3 次；第四次解析失败进入 `Paused/WAITING_FOR_USER` 并保留活动 SubAgent/handoff。
- ✅ 新 `UserMessage` 创建 turn 时把计数归零；本地 `json_repair` 不计数；`model_calls` 与默认 100 次 `AGENT_MAX_MODEL_CALLS` 契约不变。
- ✅ `SessionSnapshotCodec` 写入 `format_repairs_used`，同时写由该值投影的 `repair_attempted` bool；恢复优先使用严格非负整数计数，缺失时把旧 bool 映射为 0／1，保持 schema_version=2 与代码回退可读。
- ✅ 更新 `test_runtime.py`：覆盖同回合三次 repair、第四次暂停、一次 repair 成功→工具→后续错误仍可第二次 repair、新 turn 清零、调用上限和 handoff 下暂停不闭合；定向测试 26/26 通过。
- ✅ 更新 `test_session_codec.py`：覆盖新计数 round-trip、旧 bool 快照兼容、双写投影、非法负数／bool-as-int／错误类型拒绝；定向测试 8/8 通过。

### 4. 工程验证、提交与用户 smoke 门禁

- ✅ 全量验证完成：bootstrap 定向测试 21/21、完整 unittest 287/287、`compileall` 与 `git diff --check` 通过；旧 fixture 迁移独立提交为 `b7bb7e9`。
- ✅ 后续复核证明核心修正必须把原白名单外的 ConversationCodec 纳入共同 Entity 映射，并让 OutputFormat 对齐现有 InputFormat；已按停止规则暂停，当前最小清单由决策 249 最终取代。
- ✅ `b7bb7e9` 与 `50cde77` 只保留为首轮实现的代码／文档 checkpoint 历史证据，不再代表可以进入真实模型验收。
- ⛔ 按首轮 R8-F 执行用户 smoke —— 已由决策 248 撤回，必须先完成 R8-F-C。
- ⛔ 按首轮 R8-F 记录完成态 —— 已由 R8-F-C 的工程验证、用户 smoke 与完成态 checkpoint 取代。

## R8-F-C —— 单一模型消息 Entity 与双格式投影修正（已完成）

### 1. 问题确认与门禁

- ✅ 用户复核确认：InputFormat 设计保持现状；InputFormat／OutputFormat 必须同时存在，一个 Entity 只表示共同承载，不表示模型输出全部字段或把两份 Prompt 合成一份。
- ✅ 对照删除前 v1 的 `Message.to_json()`／`Message.from_llm_reply()` 与两份格式文档，确认稳定基线是“两个方向文档 + 一个 Message Entity + flat tool/event_payload”。
- ✅ 按用户要求 hard reset 到 `8111319`，撤销错误合并 Prompt 的 4 个提交；决策 249 取代决策 248 的单文件方案。
- ✅ 本会话只纠正五份活跃文档并建立 checkpoint，不修改生产代码、Prompt 或测试。
- ✅ 新会话已执行 `/project-bootstrap`，确认工作区干净、HEAD 包含决策 249；只实施本节，未检查或进入 R9。

### 2. 单一 Entity 与 codec

- ✅ 新增 `ModelMessageEventType`、immutable `ModelMessageEntity`、`ModelMessageParseError`；Entity 字段为 `id/role/timestamp/event_type/message/tool/tool_call_id/event_payload/thinking/plan_status`，可携带不序列化的本地 repair 诊断；输入和输出按方向使用不同字段子集。
- ✅ 新增 `ModelMessageCodec.encode(system_prompt, records)` 与 `parse(raw)`，集中实现 history encode 与 reply decode；旧 `ModelReply` DTO 尚待 Runtime 迁移后删除。
- ✅ history encode 保持当前五类 InputFormat 映射、tool result correlation、event_payload error object 与 plan_status；assistant thinking 继续不回放。
- ✅ reply decode 使用 flat `event_type/message/thinking/tool/event_payload`；模型不必提供 id、role、timestamp、tool_call_id、plan_status，Runtime 必须重建这些值。
- ✅ 迁移有效断言和 import 后删除旧 `conversation_codec.py`、`model_reply.py`；更新 Runtime 构造注入与 bootstrap composition，不改变 domain ConversationRecord。

### 3. 单一 MessageFormat

- ✅ `data/prompts/general_agent/07_input_format.md` 保持内容不变；不得删除、重命名或并入其他文件。已增加内容 hash 与 flat history 字段回归锁定。
- ✅ 修改独立 `08_output_format.md`：finish 使用 `event_type=finish`；tool_call 使用 `event_type=tool_call`、`tool` 与 object `event_payload`，参数直接放在 event_payload。
- ✅ finish 的 thinking 在 Prompt 中写为“通常应尽量提供简短、非空、用户可见摘要”，但 parser 继续允许省略／null／空白；tool_call thinking 可选。
- ✅ 保留 `render_output_format()`；完整 system prompt 同时包含 InputFormat／OutputFormat，Runtime repair 只注入 OutputFormat；`09_reserved.md` 继续最后。
- ✅ 保留每个 Agent 用户 turn 最多 3 次模型 repair、第四次 Paused、新 UserMessage 清零、本地 JSON repair 不计数与 snapshot bool 兼容，既有修复未回退。

### 4. 自动化、提交与用户 smoke

- ✅ 锁定 InputFormat Git blob `50ee7a2a3c6cba3ea78d3f5efc5756f93d8199e4`，并覆盖双文件存在、按 `07` → `08` → `09` 排序、repair 只读取 OutputFormat。
- ✅ Entity／codec contract 覆盖 input 五类事件、finish、tool_call、event_payload 参数、tool result correlation、plan_status、Runtime-owned 字段与 thinking 保留／剥离。
- ✅ 更新 Runtime／bootstrap 回归，证明工具调用参数、Plan、handoff、三次 repair 和第四次暂停均保持。
- ✅ 运行完整 unittest 278/278、`compileall`、`git diff --check`；静态扫描无旧 ModelReply／ConversationCodec 引用。代码由 `e05bdfa`、`29e698c`、`a8d55d7`、`077a4d2` 分片 checkpoint。
- ✅ 用户已完成并确认 R8-F-C finish／tool call 的真实 provider smoke；行为符合当前单一 Entity 与双格式投影契约。
- ✅ 用户 smoke 已通过；已同步 current／task／decision 并建立完成态文档 checkpoint，仍停在 R9 独立授权门禁前。

### 5. 已确认白名单

- 📌 生产新增：`src/get_me_in/application/model_message.py`；生产修改：`src/get_me_in/application/runtime.py`、`src/get_me_in/bootstrap.py`；生产删除：迁移后删除 `src/get_me_in/application/conversation_codec.py`、`src/get_me_in/application/model_reply.py`。`PromptRenderer` 生产行为保持不变。
- 📌 Prompt 修改：仅 `data/prompts/general_agent/08_output_format.md`；`07_input_format.md` 只读锁定，禁止修改／删除／重命名；不得创建 `07_message_format.md`。
- 📌 测试新增：`tests/get_me_in/test_model_message.py`；测试修改：`tests/get_me_in/test_prompt_renderer.py`、`tests/get_me_in/test_runtime.py`、`tests/get_me_in/test_bootstrap.py`；测试删除：`tests/get_me_in/test_conversation_codec.py`、`tests/get_me_in/test_model_reply.py`。
- 📌 文档 checkpoint：`docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/decision.md`。
- ⛔ `domain/messages.py`、`ports/llm.py`、session codec/state、provider adapter、Settings、RuntimeEvent、ToolDefinition／ToolExecutor、CLI、依赖、数据或 R9 文件不在范围；如确需修改，停止并提交最小扩展清单。

## R8 后续独立修正 —— query_memory 被动触发契约（已完成）

- ✅ 只读检查确认 `query_memory` 原 `UseWhen` 覆盖技能、经历、偏好、期望等宽泛个人信息，Main 同时以“必要时读取历史 memory”和“尽量利用 memory 减少重复询问”正向鼓励查询；Runtime 只校验 capability 与参数，不判断语义必要性。
- ✅ 用户确认新策略：Memory 不是主动个性化手段，只在用户明确要求查询已保存个人背景／技术栈／经历／偏好／期望，或完成当前任务必需的信息不在当前上下文、已先询问用户仍未获得时，才进行一次聚焦查询。
- ✅ `query_memory` 的 `UseWhen`／`DoNotUseWhen` 已明确禁止主动了解用户、补充画像、减少普通提问、确认已知信息、可选信息查询、问候／能力介绍／简单路由／闲聊、绕过用户拒绝和零命中后的近义词重试。
- ✅ Main `AgentSpec` 已同步改为优先使用当前对话；仅在用户明确要求或路由必需信息经询问仍缺失时，把 `query_memory` 作为一次针对性兜底。capability、审批、schema、handler、Memory 数据和其他 Agent 边界未变。
- ✅ ToolCatalog 与 production composition 回归锁定完整文字实际进入 Prompt；39 项定向测试、完整 unittest 280/280、`compileall` 与 `git diff --check` 通过，代码 checkpoint 为 `f6d3e37`。
- ✅ 用户已完成并确认真实 provider smoke：普通问候／简单路由不得查询 memory；明确查询个人背景时允许调用；必要信息缺失时必须先询问，未果后最多单次兜底。
- ⛔ 本修正独立于 R8-F-C，不检查、设计或实施 R9，不读取、迁移、改写或删除旧运行数据。

## R8 后续独立修正 —— 统一 HandoffContext 接收回合契约（已完成）

### 1. 语义与方向

- ✅ 用户确认统一覆盖 Main→Sub 与 Sub→Main；切换回 Main 不是会话第一轮，因此规则基于“最新输入包含 HandoffContext 的接收回合”，不基于 Agent 首轮或空 history。
- ✅ HandoffContext 是 Agent 间控制权交接摘要，不是用户消息；handoff 审批只批准切换，不等于授权接收 Agent 立即执行摘要中的动作。
- ✅ 使用同一结构化 envelope：`kind="delegate"` 表示 Main→Sub，`kind="return"` 表示 Sub→Main；字段区分原始用户请求、已确认信息、推断信息、完成工作和待用户决定。
- ✅ 任一 handoff 接收回合均禁止调用工具并必须 `finish` 等待下一条真实用户消息。delegate 接收方先复述并请用户确认／纠正；return 接收方先汇报完成／阻塞／待决定事项并询问下一步。

### 2. Prompt-only 实施

- ✅ 在 `data/prompts/general_agent/04_tools.md` 的 ToolAuthority 后新增 canonical `HandoffContextContract`，定义 envelope、接收回合和双向行为；未修改 `07_input_format.md` 或 `08_output_format.md`。
- ✅ 更新 `src/get_me_in/bootstrap.py` 中的 Main AgentSpec：创建 delegate context 时使用中性结构化摘要并区分已确认／推断；收到 return context 后本回合不得调用工具或再次路由，只汇报并询问用户。只改 AgentSpec 元数据，未改 composition 行为。
- ✅ 更新 Resume AgentSpec：收到 delegate context 后本回合不得调用 Plan、Memory、workspace 或 artifact 工具，只复述并确认；原“信息足够直接执行”和“避免为了确认而确认”仅适用于非 handoff 接收回合或用户已经确认后的后续回合。
- ✅ 更新 `switch_to_subagent.context` 与 `switch_to_mainagent.summary` 的 LLM-facing 元数据，分别要求 `kind="delegate"`／`kind="return"`，禁止使用命令式摘要暗示已经获得执行授权。
- ⛔ 不修改 Runtime、Orchestrator、CLI、Session／handoff typed state、审批、capability、handler、InputFormat／OutputFormat、依赖或数据。

### 3. 验证、checkpoint 与 smoke

- ✅ 更新 ToolCatalog／PromptRenderer／bootstrap Prompt 回归，锁定 canonical contract、双向 ToolDefinition 文字和 Main／Resume 冲突消除；既有 Orchestrator／CLI 自动推进行为保持不变。
- ✅ 50 项定向测试、完整 unittest 282/282、`compileall` 与 `git diff --check` 通过；初始文档 checkpoint 为 `43bbdfd`，文件所有权补充 checkpoint 为 `161dc39`，代码 checkpoint 为 `8dd876c`。
- ✅ 用户已完成并确认真实 provider smoke：Main→Resume 在审批后只确认而不读 workspace；Resume→Main 返回后只汇报／询问而不继续调用工具；用户下一条确认后才允许工作。
- ✅ 真实模型行为已由用户 provider smoke 验收；本修正不检查、设计或实施 R9，不读取、迁移、改写或删除旧运行数据。

## R8 后续独立修正 —— Workspace edit 行号稳定性（已完成）

- ✅ 确认 revision 只能证明文件版本一致，不能让模型获得多行插入／删除后的最新行号；成功 `workspace_edit` 后自动授权新 revision 会允许模型绕过重新读取。
- ✅ `WorkspaceAccessState` 增加 session/path/revision 级授权消费；成功 `workspace_edit` 后消费本次 read 授权，不再自动授权返回的新 revision。
- ✅ 保留失败行号／old_content 校验不写入文件，并验证失败校验后仍可使用同一 read 授权重试。
- ✅ 更新 `workspace_edit` 工具说明，明确每次成功 edit 后必须重新 `workspace_read`；保留返回 revision 以维持输出结构，但不将其视为下一次 edit 授权。
- ✅ 增加多行插入／删除导致行号漂移、授权消费和失败重试回归；定向测试 54/54、完整 unittest 295/295、`compileall` 与 `git diff --check` 通过。
- ⛔ 本修正独立于 R9，不修改 `LocalWorkspace` revision 算法、WorkspacePort、workspace_replace、旧运行数据或 R9 文件。

## R8 后续独立修正 —— tool call message 非空契约与 CLI 展示（已完成）

### 1. 设计与文档门禁

- ✅ 只读确认当前同时存在两个缺口：parser 允许 `tool_call.message=""`，且 `ToolStarted`／Renderer 不携带或展示非空 message。
- ✅ 用户确认 OutputFormat 精简、所有事件 message 代码强制非空、finish thinking Prompt-only 必填、message 使用 Markdown、thinking 使用纯文本 Panel 的完整方案。
- ✅ 确认生产／Prompt、测试与五份活跃文档白名单；本修正独立于 R9，不修改 `07_input_format.md`、snapshot schema、provider、工具或旧数据。

### 2. OutputFormat 与模型回复校验

- ✅ 删除 `<InputOutputDistinction>`，收敛单一 Schema/Requirements，明确 message Markdown 与 thinking 纯文本边界。
- ✅ `ModelMessageCodec.parse()` 对 finish/tool_call 统一强制非空、非纯空白 message，保持 finish thinking 解析宽容和既有 repair 预算。
- ✅ 更新 Prompt／codec／Runtime/bootstrap fixture 回归；定向测试 65/65、diff-check 通过，checkpoint 为 `0694c2b`。

### 3. RuntimeEvent 与 CLI 展示

- ✅ `ToolStarted` 增加必填 message，Runtime 使用关键字参数投影 message、thinking、tool 和 arguments。
- ✅ Renderer 按 thinking Panel（开启时）→ Markdown message → 脱敏工具状态展示，保持 Completed 的一致能力。
- ✅ 更新 Runtime／CLI 回归，覆盖 Markdown 一致性、thinking 纯文本／开关／顺序、Rich markup 边界和参数脱敏；定向测试 84/84 通过，checkpoint 为 `5a43fda`。

### 4. 完整验证与完成态

- ✅ 运行完整 unittest 296/296、`compileall`、`git diff --check` 与白名单审查。
- ✅ 完成 InputFormat blob、全部 ToolStarted 调用点与 production-component smoke，确认 Prompt repair、snapshot/history 与 R9／旧数据边界未漂移。
- ✅ 真实 provider／TTY smoke —— 用户分别以 `SHOW_THINKING=false` 与 `true` 验证工具调用：message 两次均显示；关闭时无思考摘要；开启时 tool call 未返回可选 thinking，finish thinking 以纯文本 Panel 显示在最终 Markdown message 上方，符合契约。
- ✅ 用户 smoke 通过后更新五份活跃文档最终完成态并建立独立 checkpoint。

## R8 完成态回归订正 —— Chroma memory／persistent 模式

- ✅ 只读确认 legacy 的 `CHROMA_PERSIST_DIR` 存在／缺失曾切换 persistent／memory，新架构无条件 persistent，属于未显式确认的能力遗漏。
- ✅ 建立专项计划与决策 271；默认保持 persistent，新增显式 `KNOWLEDGE_INDEX_MODE=persistent|memory`，旧 `CHROMA_PERSIST_DIR` 继续隔离。
- ✅ 新增 `InMemoryManifestRepository`，memory mode 使用 `EphemeralClient` 与空 process-local manifest 成对装配，每个进程全量重建。
- ✅ 保持 `KnowledgeService`、port/domain、Runtime、Tool、Session、CLI command 与公开检索协议不变；未知 mode 在 Settings 和 composition 两层拒绝。
- ✅ 自动化覆盖默认／显式／非法 mode、成对装配、构造失败清理、全量重建、磁盘不变、最后 client close，以及 persistent → memory → persistent 新增／修改／删除追平。
- ✅ 定向测试 72/72、完整 unittest 305/305、`compileall`、`git diff --check`、无 legacy path／Server／HttpClient 静态门禁通过。
- ✅ 真实 Chroma 双模式 smoke 使用项目 BAAI embedding／reranker 和显式 embeddings：persistent 重启命中 1，memory 重启命中 0。
- ✅ 计划 checkpoint 为 `e23aa4a`，代码／测试 checkpoint 为 `a5df705`；最终文档独立收口，R9 仍未授权。

## R8 完成态配置清理 —— 移除旧 RAG 环境变量别名（已完成）

- ✅ 从 `.env.example` 删除 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE` 兼容说明；正式配置继续使用 `EMBEDDING_MODEL`、`RERANKER_MODEL`、`EMBEDDING_BATCH_SIZE`。
- ✅ `Settings.from_env()` 删除三个旧名称的回退解析并简化 `positive_int()`；旧名称按未知环境变量忽略，未提供正式变量时继续使用既有 BAAI 模型与 batch size 32 默认值。
- ✅ Settings 回归同时锁定正式名称可自定义和旧名称不再生效；未修改 Settings 字段、Chroma 存储模式、Embedder／Reranker adapter、依赖或运行数据。
- ✅ Settings 定向测试 15/15、Bootstrap 定向测试 25/25、完整 unittest 306/306、`compileall`、`git diff --check` 与静态引用扫描均通过。
- ✅ 代码／测试 checkpoint 为 `df01327`；当前事实、任务与决策由独立文档 checkpoint 收口。
- ⛔ 本清理不进入 R9；`docs/task.md` 与 `docs/decision.md` 中既有旧名称只作为历史记录保留，不代表当前支持。

## R8 完成态配置治理 —— 运行配置硬编码外置（已完成并通过用户审查）

- ✅ 完成只读盘点，区分部署／运行可调参数与协议、持久化、安全不变量。
- ✅ 建立专项计划与决策 274，固定新增变量、默认值、验证规则、legacy 路径拒绝、文件白名单、E0～E5 切片和验收门禁；完成后的专项原文由 Git 历史保存。
- ✅ E0～E2 已完成；E2 定向测试 60/60、完整 unittest 313/313、compileall、diff-check 与旧硬编码静态扫描通过，代码／测试 checkpoint 为 `b424b62`。E2 checkpoint 订正 production 白名单：`retrieval.py` 沿用原白名单，新增 `application/memory_service.py`，仅接收注入的 `settings.log_file_name`。
- ✅ E3 已完成：CLI result／argument／session preview 与 workspace/customer/retrieval 五个 Tool default 均由 Settings 解析并由 bootstrap 显式注入；Tool schema 文案、default、handler fallback 同源，显式调用参数优先；定向 114/114、完整 unittest 318/318、compileall、diff-check 通过，代码／测试 checkpoint 为 `154ff4f`。
- ✅ E4 已完成：57/57 `.env` key/shape、一致配置构造、缺失／非法配置退出码 2 无 traceback、legacy refusal、persistent／memory 组件 smoke 通过；有效根入口在本地模型快照与注入 `/exit` 的 headless smoke 下退出 0。
- ✅ E5 已完成：专项计划、当前状态、设计事实、任务状态与决策记录已同步；文档独立 checkpoint 完成，计划不构成 R9 授权。
- ✅ 用户审查 P1/P2 已修复：六个时长／轮询变量统一拒绝 `nan`、`inf`、`-inf`；Settings 与 `logging_setup.py` 均显式拒绝 `/` 和 `\\`，新增 18 项非有限值断言并补充路径分隔符覆盖，完整 unittest 320/320、compileall、diff-check 通过；代码／测试 checkpoint 为 `459b1cf`。
- ✅ 用户确认运行配置专项完成，并授权将本专项、Chroma 模式订正和 R9 前质量加固三份已完成执行文档收敛；决策 278 记录删除与台账迁移，R9 仍未授权。

## R8 完成态已知暂缓维护事项（D1～D7）

以下事项由 R9 前质量加固审查确认，但不属于已完成的 Q1～Q7 实现范围。它们不得被解释为 R9 授权；只有满足对应重启条件并取得单独授权后才可实施。

### D1 —— Artifact committed replay 的文件验证

- ⏸️ **现状：** committed copy/build/merge replay 直接返回已记录结果，不验证输出仍存在或仍匹配原 hash。
- **暂缓原因：** 当前尚未维护 Artifact 版本／reconcile 生命周期，单独增加验证会引出缺失文件、内容漂移、重建和版本推进语义。
- **重启条件：** 开始 Artifact 版本维护、外部修改协调或 committed reconcile 设计时。

### D2 —— 完整 TeX 文件系统沙箱

- ⏸️ **现状：** 当前只禁用 shell escape，不保证 TeX 不能读取工作区外的本地文件。
- **暂缓原因：** 当前是本机、显式审批的简历编译流程；完整限制需要 TeX distribution 配置、受限进程或容器。
- **重启条件：** 接受不可信第三方 `.tex`、服务化、多用户部署，或要求严格文件机密边界时。

### D3 —— Rewind 同时间戳碰撞

- ⏸️ **现状：** rewind 使用时间戳确定 turn 边界。
- **接受原因：** 当前单 session、单 worker 顺序执行，用户接受现有时间精度风险。
- **重启条件：** 多进程写 session、导入外部 snapshot、批量重放或观察到真实碰撞时。

### D4 —— `AgentRuntime` 整体拆分与 `_complete_model()` 重构

- ⏸️ **现状：** Runtime 较长，但仍围绕单 Agent typed transition 内聚；`_complete_model()` 包含连续的 provider／parse／repair／state 流程。
- **暂缓原因：** 机械拆分会增加隐式状态同步和联合返回；已完成的质量加固只移除 interaction／Plan 局部硬编码。
- **重启条件：** 新增第二类 runtime executor、方法复杂度继续增长，或可以提取真正纯逻辑时。

### D5 —— ChromaDB 公告无可升级版本

- ⏸️ **现状：** 当前锁定 `chromadb 1.5.9`；质量加固依赖审查记录的 Chroma Server 预认证代码注入公告当时没有更高可用修复版本。
- **接受边界：** production 只使用嵌入式本地 `PersistentClient`／`EphemeralClient`，不得暴露受影响 Server／API 路径；memory index 订正不改变该网络不可达边界。
- **重启条件：** 上游发布修复、架构考虑远程 Chroma，或 dependency audit 信息变化时。

### D6 —— 原始模型回复日志

- ⏸️ **现状：** 格式解析失败时以 WARNING 保存完整 `raw_reply`。
- **接受原因：** 用户明确要求保留完整响应以定位 JSON 解析和 provider 输出问题。
- **重启条件：** 多用户／服务化部署、日志集中上传、日志访问边界变化或需要自动脱敏时。

### D7 —— 其余可读性与维护性审查

以下项目尚未达成具体改造方案，必须单独审查，不得顺手混入其他阶段：

- ⏸️ application／CLI 多处依赖标注为 `object`，现有 Port／Protocol 未贯穿所有边界。
- ⏸️ `bootstrap.py` 内嵌 Main AgentSpec、重复构造 Main／Resume Runtime，以及进程级环境变量副作用。
- ⏸️ `KnowledgeService.reload()` 的重复线性查找和逐 source 整体 manifest 写入。
- ⏸️ `JsonArtifactRepository.next_version()` 每次扫描完整历史。
- ⏸️ `BackgroundWorker._results` 终态结果不淘汰。
- ⏸️ Memory JSON 写入原子性、损坏记录隔离和仓库错误一致性。
- ⏸️ Ruff、静态类型检查、安全扫描、复杂度／覆盖率门禁是否纳入项目。
- ⏸️ 大量压缩为单行的 handler／service 代码是否统一格式化。

## 当前基线维护修正 —— Knowledge 取消作用域（已完成）

- ✅ K0：从 2026-08-03 真实日志、当前代码与 Git 历史完成只读诊断；确认普通 Runtime 取消广播误伤 startup Knowledge，且问题发生在 manifest load 前，不是 `data/runtime/` 迁移或索引损坏。
- ✅ K0：建立 Knowledge 取消作用域修复的目标契约、推荐实现、文件白名单、回归矩阵、真实 smoke、提交与停止门禁；历史计划由决策 280 和 Git 保留。
- ✅ K1：在 `Application` 内实现实例级、锁保护的私有 active cancellation target；RuntimeCommand 只取消 Session，ReloadKnowledge 只取消 Knowledge，其他 ApplicationCommand 不广播取消；公开 API 不变。
- ✅ K2：让 `KnowledgeService.reload()` 区分 `InterruptedError` 与真实 failure；startup cancellation 可重试，READY／DEGRADED reload cancellation 保留原可查询状态，worker-owned cancellation 映射为 `CANCELLED`。
- ✅ K3：补充普通 Runtime／ReloadKnowledge 取消路由、active target 清理、prepare 阶段取消、状态保留、重试和 worker job-state 回归；真实 prepare failure 仍须为 `ERROR`／`FAILED`。
- ✅ K4：运行定向与完整 unittest、compileall、diff-check；完成 cold-start 普通对话取消、`/ragreload` 取消／重试、prepare 中 `/exit` 三组 production composition smoke。
- ✅ K5：用户确认上述三项真实终端测试无问题；已更新五份核心文档、追加决策 283、删除临时专项计划并完成文档收口。
- ⛔ 本修复不得修改 R9 设计／代码，不得读取、改写、迁移或删除四个 legacy 数据目录；扩展代码白名单、公开 API、依赖或数据路径前必须停止确认。

## 当前基线多语言支持 —— UI locale 与模型回复语言（已完成）

- ✅ L0：完成当前代码、Prompt、UI、Memory 检索和文档结构的只读审查；确认 UI 使用 locale loader／命名占位符，模型使用独立 ResponseLanguage 注入，不维护多份完整 system prompt。
- ✅ L0：建立多语言专项执行计划，固定 `zh-CN`／`en-US`、两个进程级语言配置、完整新类型、逐切片文件白名单、禁止清单、测试矩阵、真实 smoke、checkpoint 和停止门禁；历史计划由 Git 与决策 284～293 保存。
- ✅ L0：用当前 production Chroma、embedding 和 reranker 完成两组英文→中文 Memory 查询对照；技术栈与年龄均正确 Top-1。本证据不修改 Memory／索引，也不替代真实模型工具调用 smoke。
- ✅ L1：新增 typed Locale、strict catalog loader、zh-CN／en-US catalog，以及 `UI_LOCALE`／`MODEL_RESPONSE_LANGUAGE`／`LOCALES_DIR` Settings；解决 Settings 解析前诊断 Renderer 的 bootstrap locale 顺序。代码／测试 checkpoint 为 `21ccef3`；用户批准将仅含新增必填 Settings fixture 字段的 `tests/get_me_in/test_bootstrap.py` 纳入 L1 测试白名单；333 项 unittest、compileall、diff-check 通过。
- ✅ L2：完成 Renderer、InputController、CommandRegistry、CliApp、WorkerRunner 和 application result presentation 的本地化；保持命令名、Rich／Markdown／escape、thinking Panel 和参数脱敏契约。代码／测试 checkpoint 为 `a868252`；完整 unittest `338/338`、compileall、diff-check 和 L2 精确白名单审查通过。
- ✅ L3：用 `ProgressKind` 和 canonical tool name 替代固定英文 Progress／审批展示文本；前端按 stable code 翻译，Application／domain 不依赖 CLI Translator，snapshot 与取消 reason 不变。代码／测试 checkpoint 为 `cfca149`；完整 unittest `338/338`、compileall、diff-check 和 L3 精确白名单审查通过。
- ✅ L4：新增 `07_response_language.md` 与 `RESPONSE_LANGUAGE` 注入；Main／Resume 使用相同 resolved locale，`08_input_format.md`／`09_output_format.md`／`10_reserved.md` 保持顺序，ModelMessageCodec 和 format repair 不变。代码／测试 checkpoint 为 `8dc56a5`；完整 unittest `340/340`、compileall、diff-check、Prompt 静态 contract 和 L4 精确白名单审查通过。
- ✅ L5：定向验证 `151/151`、完整 unittest `346/346`、compileall、diff-check、catalog／Prompt 静态 contract 和 fake/headless component smoke 已通过；已补充语言配置中文默认行为、`.env.example` 选项注释，并将 general_agent Prompt 编号重排为 `01`～`10`；代码／测试提交为 `a5efaa1`、`c4ac8dd`、`02c9c5d`。用户已确认双语言真实 provider／Windows TTY 体验无大问题，其中英文 Memory smoke 遵循既有被动契约，不触发 Memory build。
- ✅ L6：用户审查完成；README、五份核心文档和完成决策已更新并独立提交。最终事实迁入核心文档后，已按用户授权删除完成态专项执行文档；本专项完成且不进入 R9。
- ⛔ 首版不增加 `/language`、自动语言检测、Session locale／schema、Prompt 多语言副本、Memory build 改造、embedding／Chroma 变更、依赖或数据迁移；本专项独立于 R9。

## B00 —— 交互式 Runtime token usage（已完成设计，暂缓实施）

- ✅ 固定交互式 Agent Runtime actual-attempt 范围、Session 顶层 lifetime ledger、logical call／1-based attempt identity、typed usage／unknown／outcome、rewind 与 SubAgent closure 不回滚边界。
- ✅ 固定 Orchestrator 显式 attempt scope、response envelope、post-response completion、可选 response model、OpenAI timeout adapter 映射，以及 RuntimeTransition → SessionTransition → SessionService 同次提交链路。
- ✅ 固定 schema v3 可选 ledger 与单向兼容风险；严格校验 identity、logical-call 分组、cache 子集、provider total、Decimal 字符串和单一计费单位，不恢复 v2、不升级 v4。
- ✅ 固定 provider usage、context estimate 和参考费用三条独立口径；全局 context 配置及估算缓冲由配置者负责，preflight pause 不发请求／不增 `model_calls`，普通消息继续追加，`/rewind` 显式后退。
- ✅ 固定整组可选费用配置与 `CostUnavailable(NO_PRICING)`；单位变化时保留 usage 并按当前 profile 单价重算历史已知费用，不做汇率换算。
- ✅ 固定独立 `/usage` typed Application view、最近 10 条、隐私边界、MemoryExtractor 永久排除，以及精确 production／测试白名单和 16 项验收矩阵；新增真实 provider smoke 与 estimator／真实 input token 对照校准。
- ⏸️ production／测试实现仍未授权。未来必须由用户按 `docs/interviewer-agent-review.md` B00 白名单单独授权；禁止借 B00 修改 Memory、其他 provider 能力、Interviewer production、compression、依赖、legacy 数据或任何白名单外文件。

## R9 —— 重构后功能（不在当前执行范围）

### 1. InterviewAgent Workflow 前置 Review

- 📌 确认 Workflow 与 Hub-and-Spoke 的层次边界：Workflow 是 InterviewAgent 内部执行策略，不改变 Main 唯一调度和禁止子 Agent 直连的规则。
- 📌 复核 Orchestrator 对具体 `AgentRuntime` 的耦合；如确有需要，先提交最小 typed executor protocol 的文件、类和公开方法清单。
- 📌 设计 typed/versioned Interview workflow state；至少表达 workflow version、稳定 step id、当前问题、回答、评分进度、等待原因和终止原因。
- 📌 决定 Session agent-local state 使用 tagged union 还是 typed envelope；`SessionState` 继续是唯一长期状态源，不允许 runtime 私藏 workflow 状态。
- 📌 决定“等待下一次自由文本回答”复用 `Completed` 还是新增最小 RuntimeEvent；同步明确 finalize、snapshot 和 auto-memory 的触发时点。
- 📌 固定 save/restore/rewind、暂停、取消、退出和 main → interview → main handoff closure；恢复不得重放已完成副作用。
- 📌 固定原始回答、逐题评分、最终报告与 question/rubric 的 Session／Artifact／Memory／Knowledge 所有权。
- 📌 在持久化前确认敏感数据脱敏、删除入口与 retention；不得默认把面试记录写入 Memory 或普通日志。
- 📌 确认采用项目内“确定性 Workflow 外壳 + 节点内 LLM”；若希望引入外部 workflow engine，单独重开依赖与架构决策。
- 📌 提交并确认 InterviewAgent 新文件、类、构造依赖、公开方法、snapshot migration 与独立实施切片；确认前不得 coding。

### 2. InterviewAgent 推荐实现与验证方向

- 📌 建立有界流程：准备 → 出题 → 等待回答 → 评估 → 追问或下一题 → 汇总 → 返回 Main。
- 📌 为题数、追问数、模型调用和失败重试设置显式上限；workflow branch/loop 由纯 transition 决定。
- 📌 复用 RuntimeCommand/RuntimeEvent、capability、ToolOutcome、CancellationToken、ResourceStack 和现有 handoff closure；只在现有协议无法表达需求时增加最小类型。
- 📌 为副作用 node 定义 operation key 或 pending → effect → commit；snapshot 只保存可安全恢复的稳定点。
- 📌 增加 workflow transition/property tests，覆盖分支、循环、用户输入、取消、restore/rewind 和错误恢复。
- 📌 使用真实 LLM smoke 验证中文／英文面试、追问质量、评分、报告以及完整 main → interview → main 链路。

### 3. 其他暂缓功能

- 📌 CLI banner 客制化：在独立清单确认后评估 `CLI_BANNER_ENABLED`、标题、副标题与样式配置；配置文本必须按普通文本安全渲染，不得默认解释为 Rich markup，也不得把主题配置混入 Runtime/Application。
- 📌 Job Search 产品方案与数据源。
- 📌 LearningAgent。
- 📌 Sticky Plan。
- 📌 多会话并行或其他前端。

每项开始前必须独立讨论设计与方法清单，不能因已列在此处而自动实施。

## 重构完成定义

- 主入口覆盖当前已实现能力，完整 smoke matrix 通过。
- Runtime、Session、Tool、Knowledge、Memory、Workspace、CLI 边界均通过公开协议协作。
- 无可变全局运行时单例、无 import-time 注册、无 CLI→Agent 私有字段访问。
- 无魔法控制 dict；handoff/approval/cancel/failure 为明确类型。
- Agent 元数据声明式，普通新 Agent 不需要复制 14 个方法。
- Session/Memory/Artifact 持久化有 schema version 和 migration 说明。
- 旧实现与兼容层已删除，文档与实际 Catalog 一致。
- 用户完成成果审查并执行 `/project-checkpoint`。
