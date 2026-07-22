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
- ⬜ 创建 CliApp，仅保留输入循环和 application command/event 转发。
- ✅ 创建 CommandRegistry，命令帮助与 handler 同源。
- ⬜ 创建 InputController，管理 autocomplete/history/prefill/editor。
- ⬜ 创建 Renderer，管理 Markdown/Plan/spinner/error/recap。
- ⬜ 创建 WorkerRunner，使用单 worker 串行调用 Application，跨线程只调用公开 `request_cancel()`。
- ⬜ 创建 `cli/main.py` 与 `cli/__main__.py`，提供 `python -m src.get_me_in.cli` 独立入口。

### 2. 命令迁移

- 🔄 `/help`
- 🔄 `/edit`
- 🔄 `/dump`
- 🔄 `/restore [session_id]`
- 🔄 `/rewind`
- 🔄 `/ragreload [target]`：R5 先注册并明确报告 R6 尚不可用，R6 再接真实 handler。
- 🔄 `/build-memory`：R5 先注册并明确报告 R6 尚不可用，R6 再接真实 handler。
- 🔄 `/exit_sub`
- 🔄 `/approval prompt|auto`；保留 `/auto-approve-switch` 兼容 alias，策略只决定 ApprovalRequested 是否自动 Approve。
- 🔄 `/exit`

### 3. Interaction 与跨平台

- ⬜ ApprovalRequested → questionary confirm/select → Approve/Reject command。
- ⬜ SelectionRequested → 选择/自定义输入 → SubmitSelection command。
- ⬜ 删除 UIBridge 和模块级 current bridge 的 v2 依赖。
- ⬜ Windows UTF-8、Esc、Ctrl+C、EOF 和 editor-not-found 行为验证。
- ⬜ Input history 使用进程内 CLI-owned state；restore 后从 `SessionView.rewind_points` 重建，不增加独立持久化 schema。
- ⬜ Completed/Failed/Cancelled 后自动 snapshot；保存失败单独渲染且不得覆盖原终态。
- ⬜ HandoffRequested 后发送 Continue，验证目标 Runtime 已由 Orchestrator 启动。
- ⬜ G5 通过后删除临时 `scripts/v2_runtime_smoke.py`。
- 📌 Sticky Plan：Renderer 稳定后评估，默认不阻塞 G5。
- ⬜ 完成 G5 验收。

## R6 —— Knowledge/RAG 与 Memory

### 1. Knowledge/RAG

- ✅ 保留 R3 已定义的 tool-facing RetrievalPort 与 RetrievalResult，不在 R6 重复创建。
- ⬜ 定义 KnowledgeSource、SearchQuery、SearchResult、KnowledgeSourceRepository、KnowledgeIndexPort 与 ManifestRepository。
- ⬜ 显式装配 ChromaStore/Embedder/Reranker/Loader。
- ⬜ 将 start/is_ready/search/reload/load_file/delete 收敛到 KnowledgeService。
- ⬜ 设计 manifest：source path、collection、content hash、mtime、chunk ids、status。
- ⬜ 正确处理新增、修改、删除和重命名。
- ⬜ 明确 loading/error/ready 状态的并发语义。
- ⬜ 实现 close 和后台任务等待。
- ⬜ 让 KnowledgeService 适配现有 RetrievalPort，并通过 `CommandRegistry.replace()` 接入 `/ragreload` 真实 handler。
- ⬜ composition root 使用统一逆序资源清理栈，不在 Application.close() 逐项硬编码 adapter。

### 2. Memory

- ⬜ 定义 MemoryRepository 与 versioned Memory DTO。
- ⬜ MemoryExtractor 依赖 LLMPort，不直接创建 PromptLoader/LLMClient。
- ⬜ MemoryService 显式执行 extract → write → index。
- ⬜ 索引失败记录 pending/error，并支持重试。
- ⬜ search/delete 通过公开 service，不延迟 import RAG facade。
- ⬜ 通过 `CommandRegistry.replace()` 接入 `/build-memory` 真实 handler。
- ⛔ 保持 v1 Markdown memory 可读 —— R-D6 明确不迁移旧 Memory。
- ⬜ 完成 G6 验收。

## R7 —— Resume 纵向切片

### 1. Agent 与 capability

- ⬜ 将 ResumeAgent 的 14 个方法转换为 AgentSpec。
- ⬜ 为 Resume AgentSpec 组合 R3 已有的 workspace.read/write/open、resume.artifact、interaction、plan 等 capability；仅在有明确最小权限收益时再拆 template.copy/pdf.build。
- ⬜ 保留新建/修改/JD 定制三类入口行为。
- ⬜ 保留“编辑前读取”和“不得编造经历”的约束。

### 2. Artifact service

- ⬜ 定义 Artifact、ArtifactKind、ArtifactRepository。
- ⬜ 以 ArtifactService-backed adapter 替换临时 ResumeArtifactPort 实现，保持既有工具签名和 ToolOutcome 闭合协议。
- ⬜ copy_template 在现有模板复制结果上记录源模板、目标 LaTeX 和 README。
- ⬜ build_pdf 复用现有 ProcessRunner，新增 stdout/stderr/exit code 和 PDF artifact 记录。
- ✅ workspace_open 已在 R3 通过 Frontend/OS adapter 实现，不由 domain 直接启动 GUI；R7 只做端到端复验。
- ⬜ 区分 user memory 与 resume artifact/version。

### 3. 端到端验证

- ⬜ 中文模板新建 → 填充 → 编译 → 预览。
- ⬜ 英文模板新建 → 填充 → 编译 → 预览。
- ⬜ 双语模板复制与文件名防重复后缀。
- ⬜ 修改已有简历与精确 edit/replace。
- ⬜ pdflatex 缺失、超时、编译失败与修复。
- ⬜ 审批拒绝、Esc cancel、save/restore/rewind。
- ⬜ 完成 G7 验收。

## R8 —— 切换与清理

### 1. 入口切换

- ⬜ `main.py` 切到 v2 bootstrap，单独提交。
- ⬜ 确认 G6、G7 均已通过；不得仅因 Resume 主路径通过而跳过 Knowledge/Memory 门禁。
- ⬜ 运行完整 capability parity matrix。
- ⬜ 验证 `data/reference/`、`data/prompts/`、`data/resume/template/` 可直接作为 v2 静态输入。
- ⬜ 确认 v2 不读取 `data/save/`、`data/memories/`、`data/chroma/` 或 `data/temp/`。
- ⬜ 将入口切换与遗留删除拆为两个独立提交；入口切换提交是删除前回退点并由用户审查。

### 2. 遗留删除

- ⬜ 删除旧 BaseAgent/MainAgent/ResumeAgent/JobSearchAgent 实现。
- ⬜ 删除旧 App/Handler/Request/Response/UIBridge。
- ⬜ 删除旧 ToolRegistry 与 import-time tool registration。
- ⬜ 删除旧 RAG/Memory 全局 Facade 和兼容 adapter。
- ⬜ 删除废弃 PlanStatusInfo、CONFIRM_APPROVED、SELECT/CONFIRM 协议分支。
- ⬜ 删除源码目录中的 `.ipynb_checkpoints`。
- ⬜ 确认临时 `scripts/v2_runtime_smoke.py` 已随 R5 正式 CLI 落地删除。
- ⬜ 移除所有 v2 → legacy imports。

### 3. 文档与状态

- ⬜ 将落地架构更新到 `docs/design.md`。
- ⬜ 将已完成迁移更新到 `docs/plan.md` 和 `docs/task.md`。
- ⬜ 将关键重构决策追加到 `docs/decision.md`。
- ⬜ 更新 AGENTS.md 中的架构、命令、约定和工具数。
- ⬜ 使用 `/project-checkpoint` 更新 `docs/current.md`。
- ⬜ 完成 G8 验收。

## R9 —— 重构后功能（不在当前执行范围）

- 📌 InterviewAgent。
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
