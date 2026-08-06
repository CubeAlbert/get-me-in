# 当前状态

**当前阶段：** R9-P 前置 Review 继续进行；B-01 SubAgent 单次 handoff 无状态生命周期已验证关闭，B00 token usage 的完整方案、实施白名单与验收矩阵已确认但按用户要求暂不实施；Interviewer 与 B00 production／测试实现仍未授权

**当前任务：** 继续 [`docs/interviewer-agent-review.md`](interviewer-agent-review.md) 的 B03，讨论最小 typed executor protocol 与 Interviewer agent-local state 形状；当前只讨论方案，不进入 coding

**当前子任务：** 从 B03 的 Orchestrator 最小 executor contract 开始，明确通用 `AgentRuntime` 与未来 Interviewer workflow executor 需要共享的 command／transition／state 能力，并区分持久化 agent-local state 与只存在于一次调用期间的 transient state。

**当前阻塞：** 当前没有技术硬阻塞；B03～B12 仍需逐条完成前置 Review。B00 已决定但暂缓实施；B00、Interviewer、context compression 与其他 production／测试实现均未授权。

**会话交接说明：** B-01 由 `cdb45e2` 实现 fresh-start／closure-destroy、typed start／close signal、Plan／rewind 协调和 schema v3；`96fa690` 关闭严格 schema 审查 finding，`6b0837f` 隔离 CLI 单测与真实 `.env`，完整 unittest 356/356、compileall、diff-check 与 import-boundary 已通过。B00 已确认并经审查修订：只统计交互式 Runtime actual attempts；Session 顶层 lifetime ledger 不随 rewind／SubAgent closure 回滚；Orchestrator 显式传 attempt scope，adapter 保留 response metadata 并映射 OpenAI timeout；schema v3 接受旧代码降级丢失 ledger 的单向兼容风险；context 配置与启发式缓冲由配置者负责，pause 后普通消息继续追加且可 `/rewind`；费用配置整组可选，缺失时为 `CostUnavailable(NO_PRICING)`，单位变化按当前配置重算；MemoryExtractor 永久排除。精确 production／测试白名单与 16 项验收矩阵已写入 tracker，包含真实 provider smoke 和 estimate 对照校准，但用户明确要求暂不实施。

**下一步：** 从 B03 开始逐条讨论：先确定 Orchestrator 面向 executor 的最小 typed protocol，再确定 Interviewer 持久化 state envelope 与 transient execution state；只更新方案与 tracker，形成 Interviewer 精确白名单并获得单独授权前不实施。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

301. **完成 B00 token usage 审查修订并同步核心文档** — 保留用户承担 context 配置／估算缓冲和 schema v3 单向兼容风险；新增显式 attempt scope、response envelope、OpenAI timeout 映射、严格 ledger invariant、整组可选费用与 `CostUnavailable(NO_PRICING)`，确认 pause 后继续追加并将验收扩为 16 项；B00 仍暂缓实施，下一步继续 B03。
300. **完成 B00 token usage 方案并暂缓实施** — 固定交互式 Runtime attempt ledger、typed usage／outcome、schema v3、rewind、参考费用与计费单位、`/usage`、context preflight guard、MemoryExtractor 排除边界、精确实施白名单和初始 14 项验收矩阵；后由决策 301 完成审查修订，production／测试仍未授权。
299. **完成 B-01 无状态 SubAgent 生命周期修复并恢复全量测试环境隔离** — `cdb45e2`／`96fa690` 完成 fresh-start、closure-destroy、Plan／rewind、严格 schema v3 与旧 schema 隔离；用户 smoke 和 Codex 两轮审查关闭，CLI main 单测不再读取真实 `.env`，完整 unittest 356/356 通过，下一步回到 B00 方案讨论。
298. **完成 B-01 修复设计并授权下一新会话按白名单实施** — 使用 handoff `call_id` 标识 episode，增加 typed start／close signal，committed closure 后清空 target 与 Plan，Cancel／Paused 和 active snapshot 保留；schema 升 v3 并拒绝／隔离 v2，精确四个 production 文件、五个测试文件与验收矩阵已固定。
297. **恢复 SubAgent 单次 handoff 无状态契约并提升为 B-01** — 历史决策与用户确认均要求 SubAgent 仅在 active handoff 内保留多轮上下文，closure 后销毁并在下次 delegate 全新开始；当前 v2 跨 handoff 保留 history／plan 属于设计漂移，优先级高于 B00 token usage，当前只讨论方案。
296. **关闭 B02 Workflow 控制流并置顶 B00 token usage 方案审查** — 固定阶段、5 主问题／每题 1 次且全场 3 次追问、异常回答／提示／拒答、隐藏评估、partial 路径和 10 次逻辑调用／20 次实际请求上限；新增 B00 优先设计逐次 LLM token usage 的统计与查询，当前未授权实现。
295. **关闭 B01 InterviewerAgent MVP 产品契约** — canonical 名称固定为 `InterviewerAgent`／`AgentKey.INTERVIEWER`；MVP 使用用户提供的 JD 与简历摘要，由同一 LLM 完成出题和判断，不开放外部 tool call，结束后按稳定模板统一报告；默认语言／5 题、typed partial 退出、无计时执行和未来 Observer／计时扩展边界一并固定。
294. **启动 R9-P InterviewerAgent 前置 Review 并建立阻塞点追踪** — 用户授权展开 R9 前置审查，但未授权 production／测试实现；当前代码审计确认 12 个 coding 前阻塞点，新增 `docs/interviewer-agent-review.md` 作为逐条讨论入口，并继续固定 Hub-and-Spoke、typed state、隐私与 legacy 数据边界。
293. **合并多语言专项最终事实并删除已完成执行文档** — 删除已完成的 `docs/multilingual-support.md`，移除核心文档中的活跃链接和保留措辞；当前架构、配置、边界、验证与 R9 门禁继续由 README、五份核心文档、Git 和决策 284～292 保存。
292. **完成多语言专项 L6 收口并保留专项文档** — 用户确认双语言真实 provider／Windows TTY 体验无大问题；代码／测试审查修复提交 `02c9c5d`，完整 unittest 346/346、compileall、diff-check 通过；README、五份核心文档和本决策记录完成收口；专项文档当时按用户要求保留，后由决策 293 授权删除。
