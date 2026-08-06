# 当前状态

**当前阶段：** R9-P 前置 Review 继续进行；B-01 SubAgent 单次 handoff 无状态生命周期已实现、smoke、审查并验证关闭，当前回到 B00 token usage 方案讨论，Interviewer 与 B00 实现仍未授权

**当前任务：** 继续 [`docs/interviewer-agent-review.md`](interviewer-agent-review.md) 的 B00，固定逐次 LLM token usage 的数据类型、写入时序、transcript／working-context 分层、schema v3 可选字段与精确实现白名单；当前只讨论方案，不进入 coding

**当前子任务：** B00 已确认 Session 顶层 lifetime ledger、actual attempt／logical call、typed unknown、`/usage`、rewind 不回滚真实消耗，以及每 Agent context guard／95% 阈值；下一项从 provider-neutral usage record 与 attempt 写入顺序开始逐条确认。

**当前阻塞：** 当前没有技术硬阻塞；B00 尚有数据类型、写入原子性、持久化分层和精确白名单需要用户逐条确认，B03～B12 继续等待前置 Review。B00、Interviewer、context compression 与其他 production／测试实现均未授权。

**会话交接说明：** B-01 由 `cdb45e2` 实现 fresh-start／closure-destroy、typed start／close signal、Plan／rewind 协调和 schema v3；`96fa690` 关闭审查发现的 malformed schema 静默隐藏与 legacy `turn_id` 回填。用户确认 smoke 已完成，Codex 复审无新增 finding。完整 unittest 曾因真实 `.env` 的 `UI_LOCALE=en-US` 污染 CLI 单测失败，现已让 `CliMainTests` 清空／恢复环境并 mock `load_dotenv()`；完整 356/356、compileall、diff-check 与 import-boundary 通过。B00 的 owner、`/usage`、rewind 和 context guard 结论保持不变，仍未授权实现。

**下一步：** 从 B00 的 provider-neutral usage record 开始，逐条确认 token 字段、attempt outcome、logical call identity 与“provider 返回／抛错后何时写入 Session ledger”的原子顺序；只更新方案与 tracker，形成精确白名单并获得单独授权前不实施。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

299. **完成 B-01 无状态 SubAgent 生命周期修复并恢复全量测试环境隔离** — `cdb45e2`／`96fa690` 完成 fresh-start、closure-destroy、Plan／rewind、严格 schema v3 与旧 schema 隔离；用户 smoke 和 Codex 两轮审查关闭，CLI main 单测不再读取真实 `.env`，完整 unittest 356/356 通过，下一步回到 B00 方案讨论。
298. **完成 B-01 修复设计并授权下一新会话按白名单实施** — 使用 handoff `call_id` 标识 episode，增加 typed start／close signal，committed closure 后清空 target 与 Plan，Cancel／Paused 和 active snapshot 保留；schema 升 v3 并拒绝／隔离 v2，精确四个 production 文件、五个测试文件与验收矩阵已固定。
297. **恢复 SubAgent 单次 handoff 无状态契约并提升为 B-01** — 历史决策与用户确认均要求 SubAgent 仅在 active handoff 内保留多轮上下文，closure 后销毁并在下次 delegate 全新开始；当前 v2 跨 handoff 保留 history／plan 属于设计漂移，优先级高于 B00 token usage，当前只讨论方案。
296. **关闭 B02 Workflow 控制流并置顶 B00 token usage 方案审查** — 固定阶段、5 主问题／每题 1 次且全场 3 次追问、异常回答／提示／拒答、隐藏评估、partial 路径和 10 次逻辑调用／20 次实际请求上限；新增 B00 优先设计逐次 LLM token usage 的统计与查询，当前未授权实现。
295. **关闭 B01 InterviewerAgent MVP 产品契约** — canonical 名称固定为 `InterviewerAgent`／`AgentKey.INTERVIEWER`；MVP 使用用户提供的 JD 与简历摘要，由同一 LLM 完成出题和判断，不开放外部 tool call，结束后按稳定模板统一报告；默认语言／5 题、typed partial 退出、无计时执行和未来 Observer／计时扩展边界一并固定。
294. **启动 R9-P InterviewerAgent 前置 Review 并建立阻塞点追踪** — 用户授权展开 R9 前置审查，但未授权 production／测试实现；当前代码审计确认 12 个 coding 前阻塞点，新增 `docs/interviewer-agent-review.md` 作为逐条讨论入口，并继续固定 Hub-and-Spoke、typed state、隐私与 legacy 数据边界。
293. **合并多语言专项最终事实并删除已完成执行文档** — 删除已完成的 `docs/multilingual-support.md`，移除核心文档中的活跃链接和保留措辞；当前架构、配置、边界、验证与 R9 门禁继续由 README、五份核心文档、Git 和决策 284～292 保存。
292. **完成多语言专项 L6 收口并保留专项文档** — 用户确认双语言真实 provider／Windows TTY 体验无大问题；代码／测试审查修复提交 `02c9c5d`，完整 unittest 346/346、compileall、diff-check 通过；README、五份核心文档和本决策记录完成收口；专项文档当时按用户要求保留，后由决策 293 授权删除。
291. **重排 general_agent Prompt 文件编号** — `06_response_language`、`07_input_format`、`08_output_format`、`09_reserved` 依次改为 `07`、`08`、`09`、`10`；PromptRenderer 仍按文件名排序，`render_output_format()` 仍按唯一 suffix 发现；代码／测试提交 `c4ac8dd`，全量 unittest 341/341 通过。
290. **补充多语言 Settings 中文默认值** — `UI_LOCALE` 缺失默认为 `zh-CN`，`MODEL_RESPONSE_LANGUAGE` 缺失默认为 `ui` 并解析为中文，`LOCALES_DIR` 缺失默认为 `data/locales`；`.env.example` 已注释可用选项，代码／测试提交 `a5efaa1`，全量 unittest 341/341 通过。
