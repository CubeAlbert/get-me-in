# 当前状态

**当前阶段：** R5 —— CLI 拆分与交互迁移（启动前复审门禁）

**当前任务：** 基于 R4 实际落地边界重新 Review R5～R8，并确认 R5 新文件、类与公开方法清单

**当前子任务：** R4 复审遗留已修复并通过 104 项核心测试；正在形成 R5 新文件、类与公开方法清单（🔄）

**当前阻塞：** R5 编码尚未获准：必须先完成 R5～R8 复审、记录结论并取得 R5 新文件、类与公开方法清单确认

**下一步：** 将 R5 CLI/WorkerRunner、命令扩展、自动保存、审批策略和独立启动入口的最终清单同步到活跃文档，然后提交用户确认

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
