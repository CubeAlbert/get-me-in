# 重构任务列表

> 适用分支：`refactor`。架构目标见 `docs/refactor-design.md`，里程碑见 `docs/refactor-plan.md`。

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
- ✅ 形成 `docs/refactor-design.md` 与 `docs/refactor-plan.md`。

### 2. 用户决策

- ✅ 用户确认 R-D1：在 `src/get_me_in/` 受控重写。
- ✅ 用户确认 R-D2：v2 禁止可变全局单例和 import-time 注册。
- ✅ 用户确认 R-D3：采用 RuntimeCommand/RuntimeEvent 强类型协议。
- ✅ 用户确认 R-D4：Resume 保留直接编辑 LaTeX，增加 Workspace/Artifact service。
- ✅ 用户确认 R-D5：授权核心自动化测试。
- ✅ 用户确认 R-D6：不迁移旧运行数据，仅保留 reference/prompts/resume templates。
- ✅ 旧 Session、Memory、Chroma、temp、Plan、handoff 和 input history 可直接废弃。

### 3. 基线材料

- ✅ 建立 capability parity matrix，逐项列出输入、输出、副作用和失败行为。
- ⛔ 选取 v1 Session 样例用于 migration —— 不迁移旧会话，已由 R-D6 终止。
- ⛔ 选取旧 Memory/Workspace 样例用于 migration —— 不迁移旧运行数据，已由 R-D6 终止。
- ✅ 核对 `data/reference/`、`data/prompts/`、`data/resume/template/` 的 v2 输入边界。
- ✅ 建立 CLI smoke checklist。
- ✅ 记录旧入口可运行的基线 commit。
- ✅ 完成 G0 审查；未通过前不创建 v2 代码文件。

## R1 —— v2 骨架与 Composition Root

> 开始前先向用户列出本阶段所有新文件、类和公开方法，确认后再创建。

### 1. 包结构与依赖规则

- ✅ 创建 `src/get_me_in/` 分层目录。
- ✅ 定义 v2 import 规则：domain → 无外部 adapter；application → domain/ports；adapter → ports；CLI → application。
- ✅ 增加开发期依赖检查方式，确保 v2 不 import 旧 BaseAgent/App/UIBridge/Registry。
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
- ✅ 删除 v2 中对 `__switch__`、`__reject__`、`__cancelled__` 的需求。

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
- ✅ 重新完成 G2 验收；86 项核心自动化测试通过，临时 v2 Runtime Runner 已完成人工可用性验证。

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
- ✅ 重新完成 G3 验收；86 项核心自动化测试通过，临时 v2 Runtime Runner 已完成人工可用性验证。

## R4 —— Session Aggregate 与编排

### 1. Session model

- ✅ 定义 `AgentSessionState`、`SessionState`、`HandoffFrame`、`SessionTurnView`、`SessionView`、`SessionPreview`；R4 不提前定义 Artifact schema。
- ✅ 将现有 RuntimeState 的 history/phase/pending/model-call/repair 状态并入 AgentSessionState，SessionState 成为唯一规范状态源。
- ✅ AgentRuntime 改为 `advance(state, command) -> RuntimeTransition`，不得保留第二份长期状态；Application 对外仍一次返回一个 RuntimeEvent。
- ✅ 每个 Application 同时只管理一个活动 Session；生成真实 session id，并按 session/agent 构造 ToolContext、CancellationToken、Plan 绑定与 WorkspaceAccessState。
- ✅ Settings 增加 `sessions_dir`，默认使用全新 `data/v2/sessions/`，不得读取旧 `data/save/`。
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
- ⛔ 实现 v1 session/meta/message/plan → v2 migration —— R-D6 明确不迁移。
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
- ✅ 将复审结论与 R5 清单同步到 refactor design/plan/task/decision。
- ✅ 用户已确认 `docs/refactor-design.md#67-cli` 的 R5 新文件、类与公开方法清单；允许在新会话按清单开始编码。

### 1. CLI shell

- ✅ 第一实施切片：创建 `commands.py` 与 `test_cli_commands.py`，固定强类型 command spec/result、解析、alias、replace 和核心 command handlers；110 项 v2 核心自动化测试通过，独立提交 `151b04a`。
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
- ✅ 删除 UIBridge 和模块级 current bridge 的 v2 依赖。
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

- ✅ 对齐 `07_output_format.md`：finish 必须包含 string `thinking` 字段但允许空字符串，tool_call 可省略或为空；missing/type error 注入“具体错误 + 完整 canonical output format”并最多修复一次。
- ✅ 为 assistant `MessageRecord` 与 `ToolCallRecord` 增加可选 thinking；user/system/tool result 不产生 thinking。
- ✅ AgentRuntime 不再丢弃 `ModelReply.thinking`；Completed 通过 MessageRecord、ToolStarted 通过显式字段向前端投影。
- ✅ 保持 provider-neutral 边界：不得读取或保存 OpenAI/DeepSeek 原生 `reasoning_content`。

### 2. 上下文、snapshot 与展示

- ✅ ConversationCodec 对所有历史记录剥离 thinking，补齐多轮 finish/tool call 不回放测试。
- ✅ SessionSnapshotCodec 对 assistant message/tool call thinking 做可选 round-trip；缺失字段兼容为 `None`，不迁移 v1 Session。
- ✅ v2 Settings 增加 `show_thinking` 并读取 `SHOW_THINKING`；不得与只控制 provider 的 `llm_thinking_enabled` 混用。
- ✅ Renderer 在 show_thinking=true 且摘要非空时展示“思考摘要”，覆盖 Completed 与 ToolStarted；关闭时不展示但保留记录；最终回复先显示摘要再显示 LLM message。

### 3. 范围与 G5-F

- ✅ 初始 G5-F 只修改既有协议、Runtime、snapshot、Settings、Renderer 与测试；真实 CLI 复验后以独立 follow-up 新增 `logging_setup.py`，恢复 v2 显式日志装配与格式失败诊断，未进入 R6 范围。
- ✅ 运行完整核心自动化测试、CLI 编译与 SHOW_THINKING 开／关 smoke，独立提交修复证据：`da530dc`、`937c4ea`、`123281d`、`abae597`；最终 146 项核心测试通过，真实 v2 CLI 启停日志 smoke 通过。
- ✅ 已执行 `/project-checkpoint` 保存 G5-F 及 follow-up 结论；R6 coding 现可按已确认清单启动。

## R6 —— Knowledge/RAG 与 Memory

> ✅ R6-F 已完成并重新通过 G6：启动、取消、索引一致性、后台失败可见性、资源关闭和测试进程退出问题均已修复。该阶段随后停在 R6-T；决策 177 已在后续会话确认 R7 总体边界。

### 0. 启动确认与范围

- ✅ 基于 R5 修复后的 Application/CLI/Worker/Session 边界重新审查 R6。
- ✅ 删除重复 SearchQuery/SearchResult、v1 RagLoader Facade、MemoryService.search、observer/delayed import/daemon thread 等设计。
- ✅ 增加 ApplicationCommand RUN path、MemoryBuildSource、ResourceStack、BackgroundWorker、versioned manifest 和 R6-T 终止门禁。
- ✅ 记录 R6 新文件、对象、构造依赖和公开方法清单，并按该清单完成 R6 代码。
- ✅ 用户已确认 `docs/refactor-design.md#69-knowledge-与-memory` 的 R6 清单；在完成 G5-F checkpoint 后实施并完成 R6 coding。

### 1. Domain、ports 与 manifest diff

- ✅ 第一切片创建 `domain/knowledge.py`、`domain/memories.py`、`ports/knowledge.py`、`ports/memories.py` 与 `test_knowledge_service.py`，实现并独立提交 domain/ports/manifest diff 纯逻辑。
- ✅ 保留 R3 tool-facing RetrievalPort/RetrievalResult；仅增加 index 内部 IndexHit，未建立第二套公开搜索 DTO。
- ✅ 定义 manifest schema_version、source key、observed/indexed hash、mtime、chunk ids、status、pending operation 与 error。
- ✅ 实现纯逻辑 scan diff：新增、修改、删除、同 hash 重命名、失败后重试和幂等 no-op。
- ✅ 固定 v2 路径：`data/v2/knowledge/manifest.json`、`data/v2/knowledge/chroma/`、`data/v2/memories/`；未读取旧 Chroma/Memory 数据。

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
- ✅ Settings/bootstrap 显式装配 v2 路径、模型参数和生命周期；adapter 不读取旧全局 config。
- ✅ KnowledgeService 实现现有 RetrievalPort；ToolDefinition、RuntimeCommand/RuntimeEvent 与 tool closure 不变。

### 4. MemoryService 与一致性

- ✅ 实现 versioned JsonMemoryRepository；一条 Memory 一个新 v2 JSON 文件，不兼容读取旧 Markdown；同时实现 KnowledgeSourceRepository.scan/read，供应用重启或 index 重建时恢复 memories collection。
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
- ✅ 对照实际 v2 代码复核 R7 旧任务：当前生产 composition root 只装配 Main Runtime；Resume 工具仍使用临时 `ResumeArtifactPort`／`LocalResumeArtifacts`，尚无 Artifact schema 或 repository。
- ✅ 用户确认 R7-P dynamic session identity、Resume capability parity 与 agent-scoped Runtime/LLM ownership、独立 Artifact repository、ArtifactService/build-attempt 语义及 typed partial-failure/retry 五项总体边界。
- ✅ 闭合 R7-P：`Orchestrator` 在每次 Runtime transition 传入 `SessionState.session_id`，Runtime 仅在该 transition 内替换 immutable ToolContext scope；restore／rewind 清理真实 session 的 workspace grant，不引入第二份长期 Session 状态。
- ✅ Resume 保留除 `route` 外的 v1 capability parity；Main/Resume 分别拥有 Runtime、CancellationToken、PlanService、ToolContext 和 LLM 生命周期。
- ✅ Artifact 使用全新 `data/v2/artifacts/` 独立 repository，不写入 Memory、不加入 SessionSnapshot，也不随 rewind 回滚。
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
- ✅ repository 使用全新 `data/v2/artifacts/` 边界；路径契约为 workspace-relative，不读取或迁移旧运行数据。
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
- ✅ 同步 `current.md`、`refactor-task.md`、`decision.md` 并由决策 187 恢复 G7；继续停在 R8 独立授权门禁前。

### 8. R7-T2 审查修复（已完成）

- ✅ 当前环境重新运行 212 项自动化测试、`compileall` 与 `git diff --check`，均通过；工作区在审查前保持干净。
- ✅ 最小复现确认 exception retry 不一致：首次 backend exception 被保存为 COMMITTED attempt 后抛出；第二次同 operation key 直接返回 `ProcessResult(exit_code=None)`，`tools/resume.py::_build_pdf()` 会将其包装为 `ToolSuccess`。
- ✅ 最小复现确认 aggregate validation 不完整：`COMMITTED + BUILD_PDF + 无 build_attempt` 可通过 save/load，随后 `ArtifactService.build_pdf()` 重放泄漏非 typed `IndexError`；deterministic operation key、operation-kind result shape 与 nested 字段类型也未形成完整 invariant。
- ✅ 静态审查确认 composition construction cleanup 不完整：`build_application()` 在 ResourceStack 注册前创建 worker／Knowledge／Artifact 等 owner，部分后续构造或 injected LLM validation 失败路径不会统一关闭已创建资源。
- ✅ 修复切片 1：`JsonArtifactRepository` 的 save/load 共用校验已闭合字段类型、deterministic operation key 与 kind/status/result shape；所有损坏记录统一为 `ArtifactRepositoryError`。未改变 schema_version、公开 repository 方法或 operation key 算法。提交：`e963b11`。
- ✅ 修复切片 2：`ArtifactService.build_pdf()` 首次与重放的 backend exception／非结果状态语义已统一；相同 committed attempt 稳定映射为 `build_pdf_failed`，不再漂移为 `ToolSuccess`。未增加 ToolOutcome 字段或公开方法。提交：`e0e2041`。
- ✅ 修复切片 3：`build_application()` 使用临时 construction ownership stack 清理 ResourceStack 交接前后的失败；覆盖 runtime LLM 配置错误、Memory prompt 读取失败与 knowledge start 失败，不新增全局生命周期。提交：`6af22a3`。
- ✅ 最终运行 216 项自动化测试、`compileall` 与 `git diff --check`；真实临时工作区完成中文／英文模板复制与两份 pdflatex 编译，exit code 均为 0，记录 5 个 artifacts 与 2 个 build attempts。
- ✅ 同步 `current.md`、`refactor-task.md`、`decision.md` 并由决策 189 恢复 G7；继续停在 R8 独立授权门禁前。

## R8 —— 切换与清理

> 决策 191 已授权并完成 R8-P，决策 192 完成 R8-E；当前正在执行 R8-O。R8-O 的用户审查仍是进入 R8-D 前不可跳过的强制门禁。

### 1. R8-P —— 切换准备

- ✅ 确认 R7-T2 已完成且 G6、G7 均有效；切换前工作区干净，旧 `main.py` 未改动。
- ✅ 复核实际 Catalog：2 个 Agent（Main／Resume）、25 个 ToolDefinition、10 个 CLI 命令；分别从 `AgentCatalog`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 取证，并与 capability 文档一致。
- ✅ 验证 `data/reference/`、`data/prompts/`、`data/resume/template/` 可直接作为 v2 静态输入。
- ✅ 对旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 建立组合证据：静态扫描禁用路径／legacy-only 环境变量、sentinel project root 的 Settings 路径断言；R8-O 继续执行拒绝访问启动／smoke 边界，mtime／hash 前后证据只用于确认未改写。
- ✅ 将 `.env.example` 补齐为 `Settings.from_env()` 的实际变量、默认值与兼容别名；v1-only 变量暂放在“legacy rollback only”段，R8-O 前不得删除。
- ✅ 为当前空的 README 写过渡说明：同时记录旧生产根入口与 v2 预览入口、静态资产、新旧运行数据和回退边界；不提前宣称根入口已切换。
- ✅ 运行 v2→legacy import scan、入口前完整自动化测试、`compileall` 与 `git diff --check`；R8-P 已独立提交 `d91e37c`。

### 2. R8-E —— 根入口切换

- ✅ `main.py` 只 import `src.get_me_in.cli.main.main` 并 `raise SystemExit(main())`；已删除 legacy composition 与 import-time registration。
- ✅ `src/get_me_in/cli/main.py` 已修正过时说明；Settings 错误继续渲染并返回 `2`，composition／CLI 构造或启动的 `Exception` 以不受 `LOG_LEVEL` 高阈值过滤的 file-only 诊断记录完整 traceback、终端仅渲染简短错误并返回 `1`；正常关闭返回 `0`，关闭异常或 `CloseReport.issues` 对用户可见并返回 `1`。不捕获 `KeyboardInterrupt`／`SystemExit`，未新增第二入口或公开 API。
- ✅ `test_import_boundaries.py`、`test_settings.py`、既有 CLI/bootstrap 测试与 `test_cli_main.py` 覆盖根入口只依赖 v2、示例配置一致性、Settings 错误 `2`、启动错误 `1` 且无 traceback、`LOG_LEVEL=ERROR` 文件诊断、正常关闭 `0`、关闭异常隔离与 typed close issue 可见性。
- ✅ 未新增 `[project.scripts]` 或其他生产入口。
- ✅ R8-E 已独立提交 `9fbeabc`；该提交是遗留删除前的明确回退点。

### 3. R8-O —— 强制观察门禁

- ✅ 从 `uv run python main.py` 验证缺少／非法配置时可读错误退出且无 traceback，正常 `/exit` 返回成功退出码。
- ✅ 修复根入口切换后欢迎 banner 丢失的观察期回归：`Renderer.render_welcome()` 在首次输入前只渲染一次固定产品标识与 `/help` 提示；不扩展 `Settings` 或引入新依赖。
- ✅ 确认 v2 `ToolDefinition`／`PromptRenderer` 只保留 `name/description/type/required`，实际生产 system prompt 已丢失旧版 `purpose/use_when/do_not_use_when/expected_output`、参数说明与默认值；该问题不是 Notebook 导出遗漏。
- ✅ 核对 legacy Tool 基线仍在 `src/tools/`：9 个工具定义文件保留上述元数据，当前未被 v2 重构修改；逐项迁移审计若发现缺失或历史改写，再由用户提供原始定义。
- ✅ Tool 提示词语义修复清单已确认并实施：`ToolDefinition` 恢复 purpose/use_when/do_not_use_when/expected_output，`ToolSchema` 使用强类型 `ToolParameter` 表达 description/default/items/allowed_values/nullable；PromptRenderer 恢复 legacy `<Tool>` XML 外层与固定语义顺序，`Arguments` 内由强类型 schema 生成有序 JSON；保持 v2 capability、审批、handler 与 ToolOutcome 边界。
- ✅ 全部 25 个工具已与 9 个 legacy 定义文件一一对应并完成迁移；`workspace_edit.revision` 等 v2 已确认接口差异保留并补充准确说明，没有工具缺失，无需用户另行提供原始定义。
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
- ✅ Resume 的 Name、Description、5 条 Responsibilities、PrimaryGoal、4 条 SuccessCriteria、5 条 Priorities、7 条 legacy HardConstraints、4 条 SoftConstraints 恢复；额外保留“不得编造/夸大经历”和“不得调度其他子 Agent”两项 v2 强化硬约束，共 9 条。
- ✅ Agent metadata 修复的 32 项 bootstrap/Prompt/Catalog/orchestration 回归、完整 237 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `AGENT_METADATA_SMOKE_OK main_chars=13159 resume_chars=20806 agents=2 tools=25`，确认恢复内容实际进入 Main／Resume system prompt，且未重新引入旧 `switch_agent` 标识符。
- ✅ 定位偶发 model reply warning：模型返回了 InputFormat 风格的完整历史消息 envelope，在 `event_type=finish` 时遗漏 OutputFormat 必填的字符串 `thinking`；一次格式修复虽能恢复，但增加模型调用和延迟。
- ✅ 模型输出协议收敛为 `event_type/message/thinking/tool/event_payload` 五类业务字段；`id/role/timestamp/tool_call_id/plan_status` 明确由 Runtime 生成。解析器移除 `content + nested tool_call` 隐式兼容，按事件类型严格验证必需业务字段、类型和 finish/tool_call 条件组合。
- ✅ PromptRenderer 不再仅依赖文件名字典序：保留其他模板既有顺序，但将 `07_output_format.md` 显式置于完整 system prompt 最后；OutputFormat 增加 Input/Output 区别、完整 finish/tool_call 示例和内部字段禁用说明。
- ✅ 修正 conversation tool-call correlation：tool_call 历史使用 `id=event_id`、`tool_call_id=call_id`，对应 tool result 复用相同 `tool_call_id`；Runtime 生成的 record 保存当时 Plan 快照，ConversationCodec 投影 `{current, completed, remaining}`，SessionSnapshotCodec 对缺失 record plan 保持向后兼容。
- ✅ 用户复审后将多余字段策略改为允许列表投影：`id/role/timestamp/tool_call_id/plan_status` 和任意未知顶层字段均直接忽略，Runtime 重新生成可信内部值，不为可安全丢弃的信息消耗 repair 调用；业务字段错误仍沿用一次修复边界。
- ✅ 调整后的 62 项 Parser/Prompt/Conversation/Session/Runtime/bootstrap 定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 composition 输出 `OUTPUT_PROJECTION_SMOKE_OK chars=12825 tools=25`，确认末尾 OutputFormat 与忽略／重建规则可见。
- ✅ 定位工具结果后偶发纯文本回复：09:39:42 Resume call 3 完全未输出 JSON，Runtime 正确 repair 并在 call 4 恢复，但增加一次 provider 调用和约 45 秒延迟；v2 OpenAILLMAdapter 相比 legacy 丢失 `response_format={"type":"json_object"}` 是直接回归。
- ✅ OpenAILLMAdapter 对所有 completion 恢复 provider JSON object mode；当前调用方只有要求 JSON 对象的 AgentRuntime 与 MemoryExtractor，OpenAIWebSearchAdapter 保持独立协议。保留 Prompt OutputFormat、内部 Parser 和一次 repair 三层边界。
- ✅ provider JSON mode 的 49 项 OpenAI adapter/Runtime/Memory/bootstrap 定向测试、完整 240 项自动化测试、`compileall` 与 `git diff --check` 通过；真实 Pro 模型输出 `PROVIDER_JSON_MODE_SMOKE_OK keys=['ok']`，确认当前 provider 接受 json_object 并返回可解析对象。
- ✅ 确认 v2 ModelReplyParser 曾只使用 `json.loads`，`json-repair` 虽仍在依赖中但仅被 legacy `src/message.py` 使用；任何 JSON 语法错误都会触发额外模型调用，属于迁移遗漏。
- ✅ v2 在既有模型修复前增加本地 JSON 语法修复：标准 `json.loads` 失败后调用 `json_repair.loads`；尾逗号、物理换行等修复结果仍须为 object 并继续完整业务校验，成功时不增加模型调用。
- ✅ 保持严格输出契约：纯文本、JSON string／array、缺少 finish string thinking、错误业务字段类型或 finish/tool 冲突均不得归一化；本地 repair 失败或语义校验失败时，AgentRuntime 注入具体错误与 canonical OutputFormat 并只允许模型自修一次，第二次仍失败返回 `invalid_model_reply`。`repair_attempted` 继续承担运行时重试边界和 snapshot 持久化职责。
- ✅ 本地 repair／单次模型自修边界的 61 项 Parser/Runtime/provider/bootstrap/snapshot 定向测试与完整 244 项自动化测试通过；`compileall` 与 `git diff --check` 通过。
- ✅ 真实 production composition 的 Main／Resume system prompt smoke 通过：Catalog 仍为 25 个 Tool，完整元数据、参数约束、XML 语义顺序、Tool 块空行和 capability 隔离均可见；最新输出为 `PROMPT_XML_SPACING_SMOKE_OK main_chars=11733 resume_chars=19880 tools=25`。相关 23 项回归、完整 234 项自动化测试、`compileall` 与 `git diff --check` 通过。
- 🔄 完成基础对话、`/help`、`/edit`、`/approval`、`/dump`、`/restore`、`/rewind`、`/ragreload`、`/build-memory`、`/exit_sub`、Esc cancel 与关闭 smoke；当前已验证 `/help`、`/approval`、`/exit` 与正常关闭。
- ⬜ 完成 Main→Resume→Main、审批拒绝、Plan、Knowledge/Memory query/build/delete 与真实 Resume copy/read/edit/replace/build/open smoke。
- ⬜ 执行拒绝访问旧目录的启动／smoke 边界并对比目录 mtime／hash：分别证明没有读取和没有修改；确认 v2 只写显式 `data/workspace/` 与 `data/v2/`。
- ✅ 重新运行完整自动化测试、`compileall`、`git diff --check` 和 import scan；banner 修复后当前为 227 项自动化测试通过。
- ⬜ 用户审查 R8-O；Tool 提示词语义阻断已解除，但剩余 CLI、真实 Agent／Knowledge／Memory／Resume 与旧数据拒绝访问 smoke 完成前仍不得审查或进入 R8-D。后续未通过时以 `git revert <R8-E commit>` 回退，使用 R8-P 保留的 legacy rollback 配置恢复旧入口。

### 4. R8-D —— 遗留删除

- ⬜ 删除 `src/agents/`、`src/cli/`、`src/llm/`、`src/memory/`、`src/prompts/`、`src/rag/`、`src/tools/`、`src/utils/`。
- ⬜ 删除 `src/config.py`、`src/lifecycle.py`、`src/logger.py`、`src/message.py`、`src/request.py`、`src/response.py`。
- ⬜ 保留 `src/__init__.py`、完整 `src/get_me_in/` 与 `tests/get_me_in/`；不删除或迁移任何旧 `data/` 运行数据。
- ⬜ 再次精确复核并删除本地 `.ipynb_checkpoints/`、`src/.ipynb_checkpoints/`、`src/llm/.ipynb_checkpoints/`；当前三者均未被 Git 跟踪，作为本地清理证据而非提交内容，不得使用宽泛递归清理。
- ✅ 确认临时 `scripts/v2_runtime_smoke.py` 已随 R5 正式 CLI 落地删除。
- ⬜ 删除后再次确认 `main.py`／`src/get_me_in/` 无 legacy import，清单中的 legacy production modules 均不存在。
- ⬜ 审计 `pyproject.toml`／`uv.lock`；只移除经 import 与真实 smoke 证明未使用的依赖，无可删项则保持不变。
- ⬜ R8-D 独立提交，不与入口切换或最终文档提交混合。
- ⬜ 记录删除后的紧急回退顺序：先 revert R8-D 恢复源码，再 revert R8-E 恢复入口；禁止触碰旧运行数据。

### 5. R8-G —— 文档、状态与 G8

- ⬜ 将已落地 v2 架构更新到 `docs/design.md`，将迁移完成状态更新到 `docs/plan.md` 和 `docs/task.md`。
- ⬜ 删除 `.env.example`／README 的 legacy rollback 段；更新 `docs/capability-parity-matrix.md`、`docs/legacy-cli-smoke-checklist.md`、README 与 AGENTS.md；Agent、tool、command、配置和数据目录必须与实际代码一致，旧 `/auto-approve-switch` 等内容只保留为明确历史 baseline。
- ⬜ 同步 `docs/refactor-design.md`、`docs/refactor-plan.md`、`docs/refactor-task.md`、`docs/decision.md` 与 `docs/current.md`。
- ⬜ 完成删除后的完整自动化、静态、真实 adapter 与根入口 smoke matrix；确认旧数据保留说明和 R8-E 回退点完整。
- ⬜ 完成 G8，checkpoint 后停止，等待用户审查；不得自动进入 R9。

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

- v2 主入口覆盖当前已实现能力，完整 smoke matrix 通过。
- Runtime、Session、Tool、Knowledge、Memory、Workspace、CLI 边界均通过公开协议协作。
- 无可变全局运行时单例、无 import-time 注册、无 CLI→Agent 私有字段访问。
- 无魔法控制 dict；handoff/approval/cancel/failure 为明确类型。
- Agent 元数据声明式，普通新 Agent 不需要复制 14 个方法。
- Session/Memory/Artifact 持久化有 schema version 和 migration 说明。
- 旧实现与兼容层已删除，文档与实际 Catalog 一致。
- 用户完成成果审查并执行 `/project-checkpoint`。
