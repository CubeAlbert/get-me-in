# 当前状态

**当前阶段：** R9-P 前置 Review 中的 B-01 设计已完成并 checkpoint；下一新会话获授权先修复 SubAgent 跨 handoff 保留上下文的生命周期漂移，Interviewer 与 B00 实现仍未授权

**当前任务：** 下一新会话按 [`docs/interviewer-agent-review.md`](interviewer-agent-review.md) 的 B-01 精确白名单实施并验证 SubAgent episode fresh-start／closure-destroy；完成后回到 B00 token usage 方案，不进入 Interviewer coding

**当前子任务：** B-01 已达到“已决定（待实施）”：fresh start、typed start／close signal、closure 原子顺序、cancel／pause 保留、Plan／rewind、schema v3、放弃 v2 compatibility、精确 production／测试白名单和验收矩阵均已固定。本会话未改代码。

**当前阻塞：** B-01 设计已关闭但代码尚未修复，B00 与 B03～B12 等待其完成；白名单外改动、旧 snapshot migration、WorkspaceAccess／Artifact／Memory／Knowledge 行为变化均未授权。

**会话交接说明：** B-01 复用 handoff `call_id` 作为 episode identity，不新增 episode 类型；`SessionTransition` 仅增加 `started_agent`／`closed_agent`，Orchestrator fresh-start 并在 committed closure 后清空 target，SessionService 同步清空 PlanService。schema 升至 v3，只接受 v3；v2 不迁移、不改写、不删除，显式 restore 报 `UnsupportedSessionSchemaError`，session list 跳过旧 schema。active handoff save／restore 保留 target episode；closed、failure、abandon、通用 Main rewind 后所有 SubAgent state 为空；Cancel／Paused 保留。B00 已确认 Session 顶层 lifetime ledger、`/usage`、rewind 不回滚真实消耗、每 Agent context guard／95% 阈值与未实现压缩时 fail-closed，但仍未授权实现。

**下一步：** 新会话先执行 `/project-bootstrap`，只按 B-01 白名单分四步实施：typed lifecycle/fresh closure → Session Plan／rewind 协调 → schema v3／repository 旧文件隔离 → 定向／全量／TTY 验证与 checkpoint；任何白名单外需求立即停止并重新授权。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

298. **完成 B-01 修复设计并授权下一新会话按白名单实施** — 使用 handoff `call_id` 标识 episode，增加 typed start／close signal，committed closure 后清空 target 与 Plan，Cancel／Paused 和 active snapshot 保留；schema 升 v3 并拒绝／隔离 v2，精确四个 production 文件、五个测试文件与验收矩阵已固定。
297. **恢复 SubAgent 单次 handoff 无状态契约并提升为 B-01** — 历史决策与用户确认均要求 SubAgent 仅在 active handoff 内保留多轮上下文，closure 后销毁并在下次 delegate 全新开始；当前 v2 跨 handoff 保留 history／plan 属于设计漂移，优先级高于 B00 token usage，当前只讨论方案。
296. **关闭 B02 Workflow 控制流并置顶 B00 token usage 方案审查** — 固定阶段、5 主问题／每题 1 次且全场 3 次追问、异常回答／提示／拒答、隐藏评估、partial 路径和 10 次逻辑调用／20 次实际请求上限；新增 B00 优先设计逐次 LLM token usage 的统计与查询，当前未授权实现。
295. **关闭 B01 InterviewerAgent MVP 产品契约** — canonical 名称固定为 `InterviewerAgent`／`AgentKey.INTERVIEWER`；MVP 使用用户提供的 JD 与简历摘要，由同一 LLM 完成出题和判断，不开放外部 tool call，结束后按稳定模板统一报告；默认语言／5 题、typed partial 退出、无计时执行和未来 Observer／计时扩展边界一并固定。
294. **启动 R9-P InterviewerAgent 前置 Review 并建立阻塞点追踪** — 用户授权展开 R9 前置审查，但未授权 production／测试实现；当前代码审计确认 12 个 coding 前阻塞点，新增 `docs/interviewer-agent-review.md` 作为逐条讨论入口，并继续固定 Hub-and-Spoke、typed state、隐私与 legacy 数据边界。
293. **合并多语言专项最终事实并删除已完成执行文档** — 删除已完成的 `docs/multilingual-support.md`，移除核心文档中的活跃链接和保留措辞；当前架构、配置、边界、验证与 R9 门禁继续由 README、五份核心文档、Git 和决策 284～292 保存。
292. **完成多语言专项 L6 收口并保留专项文档** — 用户确认双语言真实 provider／Windows TTY 体验无大问题；代码／测试审查修复提交 `02c9c5d`，完整 unittest 346/346、compileall、diff-check 通过；README、五份核心文档和本决策记录完成收口；专项文档当时按用户要求保留，后由决策 293 授权删除。
291. **重排 general_agent Prompt 文件编号** — `06_response_language`、`07_input_format`、`08_output_format`、`09_reserved` 依次改为 `07`、`08`、`09`、`10`；PromptRenderer 仍按文件名排序，`render_output_format()` 仍按唯一 suffix 发现；代码／测试提交 `c4ac8dd`，全量 unittest 341/341 通过。
290. **补充多语言 Settings 中文默认值** — `UI_LOCALE` 缺失默认为 `zh-CN`，`MODEL_RESPONSE_LANGUAGE` 缺失默认为 `ui` 并解析为中文，`LOCALES_DIR` 缺失默认为 `data/locales`；`.env.example` 已注释可用选项，代码／测试提交 `a5efaa1`，全量 unittest 341/341 通过。
289. **完成多语言专项 L5 工程验证并等待真实 provider／TTY smoke** — 定向 151/151、完整 unittest 340/340、compileall、diff-check、locale／Prompt 静态 contract 和 fake/headless component smoke 通过；真实 provider／Windows TTY 矩阵仍待用户证据，L6 尚未开始，R9 仍未授权。
