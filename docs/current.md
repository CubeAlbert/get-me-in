# 当前状态

**当前阶段：** R5 —— CLI 拆分与交互迁移（前四切片已完成）

**当前任务：** 按已确认清单继续实施 R5 CLI

**当前子任务：** 第五实施切片：创建 `main.py` 与 `__main__.py`，装配正式 v2 CLI 入口、执行自动化测试与人工 smoke（⬜）

**当前阻塞：** 无；R5 清单已获用户确认，读取本文件的后续会话可按五步顺序小步实施

**会话交接说明：** 已完成第四切片 `app.py` 与 `test_cli_app.py`：CliApp 驱动 typed command/event，handoff 后 Continue，审批/选择转为 typed RuntimeCommand，并在 Completed/Failed/Cancelled 后自动 snapshot（失败单独渲染）。已补齐无参数 `/restore` 与 `/rewind` 的选择入口；尚未创建模块入口或执行人工 smoke。

**下一步：** 只创建 `src/get_me_in/cli/main.py` 与 `src/get_me_in/cli/__main__.py`，装配 `build_application()`、CommandRegistry、InputController、Renderer、WorkerRunner 与 CliApp，验证 `python -m src.get_me_in.cli` 并进行人工 smoke；G5 通过前不得删除临时 Runner。

**已暂缓：** InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan 等新功能统一放到 R9；R0～R8 只做 v2 重构

**参考文档：** `docs/refactor-design.md`（活跃设计）／`docs/refactor-plan.md`（活跃计划）／`docs/refactor-task.md`（活跃任务）／`docs/decision.md`（决策记录）

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-136: 见 decision.md
137. **`refactor` 分支采用独立 v2 受控重写** — 在 `src/get_me_in/` 建立 v2，显式装配依赖并使用强类型 Runtime 协议；不迁移旧 Session、Memory、Chroma、temp 等运行数据，只保留 `data/reference/`、`data/prompts/`、`data/resume/template/`；已授权核心自动化测试
138. **R1 骨架清单获确认后开始编码** — v2 采用 `src.get_me_in` 导入路径；首批实现 Settings、基础 ports、声明式 Agent/Prompt、CancellationToken、Application 与 composition root，并为纯逻辑建立自动化测试；R1 尚未完成 import guard 和 G1
139. **R1 临时无工具对话仅用于 G1 验证** — `Application.complete_text()` 必须显式注入 `LLMPort`，不保存 history、不支持工具或 handoff，并用 `TEMP-R1` 标注；R2 正式 AgentRuntime 落地时必须删除，不能作为正式 Runtime 演进
140. **R2 用 ToolResult 闭合暂停的工具回合** — Runtime 对已声明工具发出 `ToolStarted` 后暂停，只接受匹配 `call_id` 的 `ToolResult` 并产生 `ToolFinished` 后继续 LLM；R3 的 ToolCatalog 将替代 R2 过渡期的可用工具集合
141. **保留静态 prompt 的 JSON 在应用边界归一化** — ModelReplyParser 同时接受 v2 `content/tool_call` 与保留 prompt 的 `message/event_type/tool/event_payload` 形状，内部只输出 v2 ModelReply；不引入旧 Message 或旧 Runtime 协议
142. **system tools 通过显式 Clock 与 WorkspacePort 注入实现** — 当前时间取自注入的 Clock，工作目录由 ToolContext 中的受限 WorkspacePort 根目录解析；不再读取全局 config 或触发 import-time 注册
143. **Runtime 直接执行显式 Catalog 工具，应用独立装配 Workspace** — AgentRuntime 通过 ToolExecutor 执行 capability 允许的工具；审批经 Approve/Reject 闭合，业务失败作为 ToolFinished 结果交回模型。每个 Application 使用显式 WORKSPACE_DIR（默认 `data/workspace/`）及独立 PlanService，不复用旧 `data/temp/` 或模块级上下文
144. **文件预览经 FrontendPort 处理** — workspace_open 仅校验受限工作区路径并调用注入的 FrontendPort；OS 默认打开器位于 adapter，永不由 domain 或 tool 直接启动
145. **R3 检索工具只依赖临时 RetrievalPort** — query_memory 与 query_reference_data 保留既有筛选和输出契约，但 composition root 注入的 DeferredRetrievalAdapter 会在 R6 KnowledgeService 落地前明确返回不可用；v2 不回接旧版全局 RAG。
146. **R3 简历工具使用临时 ResumeArtifactPort** — copy_template 与 build_pdf 在 R3 经显式端口装配为可测试工具；R7 以 ArtifactService 替换适配器并记录 artifact/version，不改变工具与 Runtime 的闭合协议。
147. **架构复审撤销 G2/G3 完成结论并暂停 R4** — 现有 80 个测试虽通过，但未覆盖真实 Prompt 工具发现、消息与 call-id codec、pending call 闭合、阻塞取消、capability 隔离、session-scoped revision 和连续多工具回合；上述缺口修复并重新验收前不进入 R4 编码。
148. **G2/G3 修复完成并恢复门禁结论** — Runtime 改为 pull-driven 单事件状态机并补齐 provider-neutral conversation codec、call closure、多工具回合、真实取消、capability 隔离与 session-scoped workspace revision；86 项核心自动化测试通过，临时 v2 Runtime Runner 经用户确认可用；下一步停在 R4 设计清单确认门禁。
149. **后续设计按当前 Runtime 重新校准** — 每个 Application 同时只管理一个活动 Session；SessionState 唯一持有 AgentSessionState，Runtime 以状态转换器工作；handoff 由 CompleteHandoff/FailHandoff 闭合，rewind 使用 turn_id，snapshot 禁止重放活动副作用；CLI input history 与 Artifact schema 分别留在 R5/R7，R6/R7 可在 G5 后并行。
150. **增加强制 R5 前复审门禁** — G4 完成并 checkpoint 后，必须根据实际落地的 Application/Session/Command/Event/cancellation 边界重新 Review R5～R8，重点检查 CLI 薄层、R6 命令与资源生命周期、R6/R7 依赖及 R8 删除/回退范围；记录结论并确认 R5 清单前不得开始 R5 coding。
151. **R4/G4 已完成并进入 R5 前复审** — `SessionState` 已成为唯一状态源，Runtime 以 `advance(state, command)` 转换，Orchestrator 通过 Complete/FailHandoff 闭合原 call id；v2 snapshot 使用 schema_version=2、turn_id rewind 与安全 phase 规范化。98 项核心自动化测试通过；不更新设计/计划，先执行强制 R5～R8 复审。
152. **R4 复审补齐 handoff 启动、失败闭合与 frontend 回合投影** — Orchestrator 切换时用 context 启动目标 Runtime，子 Agent 取消/失败通过 FailHandoff 闭合原 call id；snapshot 严格校验 frame，restore 拒绝未装配 Agent，SessionView 公开只读 rewind_points。104 项核心自动化测试通过，G4 复验完成。
153. **R5 使用薄 CLI、单 WorkerRunner 与可替换命令注册** — CliApp 只驱动 typed command/event 并在终态自动 snapshot；WorkerRunner 单线程串行调用 Application，跨线程只 request_cancel；CommandRegistry 支持 R6 replace handler；输入历史不新增持久化 schema；提供独立模块入口，R8 等待 G6/G7 并拆分入口切换与遗留删除提交。
154. **R5 清单获确认并固定新会话实施入口** — 用户确认 `docs/refactor-design.md#67-cli` 的文件、对象、构造依赖与公开方法；新会话可编码，第一切片仅创建 commands.py 与 test_cli_commands.py。当前会话不编码，每步独立验证提交，不跨入 R6/R7。
155. **R5 第一切片已审查并保持交互职责后置** — `CommandRegistry`、核心 command handlers 及测试已独立提交；命令注册层可调用 Application 公开 API，但 `/edit`、`/help`、`/restore`、`/rewind` 的真实输入、渲染与无参数选择交互仍由 InputController/Renderer/CliApp 后续切片完成，不能因 handler 已登记而跳过这些任务。
156. **InputController 通过 CompletionProvider 获取动态命令补全** — `set_completions(provider)` 注入 `Callable[[], tuple[str, ...]]`，CliApp 将传入 `CommandRegistry.completions`；每次 read 动态取值，默认空元组，InputController 不依赖或持有注册表。
