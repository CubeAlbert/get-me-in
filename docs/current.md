# 当前状态

**当前阶段：** R9-P 前置 Review 继续进行；B00 token usage 设计及精确 API／类型／序列化清单已关闭并继续暂缓实施；下一项恢复 B03，Interviewer 与 B00 production／测试实现均未授权

**当前任务：** 继续 [`docs/interviewer-agent-review.md`](interviewer-agent-review.md) 的 B03，讨论 Orchestrator 面向通用 Runtime／未来 workflow executor 的最小 typed protocol，以及 Interviewer agent-local persistent／transient state 边界；当前只讨论方案，不进入 coding

**当前子任务：** 从 Orchestrator 调用 executor 所需的最小 command／transition／state contract 开始，区分通用同步执行协议、Interviewer workflow 持久化 envelope 与仅存在于一次调用期间的 transient execution state。

**当前阻塞：** 当前没有技术硬阻塞；B03～B12 仍需逐条完成前置 Review。B00 已决定但暂缓实施；B00、Interviewer、context compression 与其他 production／测试实现均未授权。

**会话交接说明：** B-01 由 `cdb45e2` 实现并验证关闭。B00 决策 300／301 的原方案经 302～304 第二轮复审补强，并由 305 完成一致性验证。决策 306 进一步固定 `domain/llm_usage.py`／`application/llm_usage.py` 的精确类型、既有 API 签名变化、依赖注入、Settings／CLI surface，以及 schema v3 `llm_attempts` 的 exact key set 与 `usage`／`cost` tagged-union JSON。新会话已无需自行发明 B00 命名或序列化形状，但 production／测试 coding 仍未授权。

**下一步：** 从 B03 的 Orchestrator 最小 executor contract 开始，明确通用 `AgentRuntime` 与未来 Interviewer workflow executor 共享的 command／transition／state 能力，再确定 persistent state envelope 与 transient state；只更新方案，获得单独授权前不实施。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

306. **补齐 B00 精确 API、类型与 schema v3 序列化清单** — 固定 module/type/field/enum、构造依赖、public query、transition propagation、Settings／CLI surface、`llm_attempts` exact key set 与 usage／cost tagged unions；新会话可直接按清单实施，但 coding 仍未授权。
305. **关闭 B00 第二轮复审并恢复暂缓实施状态** — 最终验证 decision TOC／正文、current 最近 10 条、白名单 2／16／2／11、16 项验收、active 文档术语与 diff-check 一致；B00 恢复“已决定（暂不实施）”，下一步回到 B03。
304. **删除 B00 cache-write 并关闭 replay／identity 语义** — 首版只保留 input／cached input／output 计价，固定 `REPORTED_BREAKDOWN`／`ASSUMED_UNCACHED`；相同 record replay no-op、冲突拒绝、codec duplicate 拒绝，identity 非空、timestamp 带时区且最近记录按 append order 获取。
303. **固定 B00 最小 scope taxonomy 与 context estimate 单一路径** — 删除冗余 component，固定必填 Agent／turn、可选 handoff episode 与 `RUNTIME_DECISION` purpose；preflight 和只读 `/usage` estimate 复用 Runtime 唯一 request builder，并固定公开 Application→SessionService→Orchestrator→Runtime 查询链。
302. **重开 B00 复审并补强 attempt／usage／cost 合法组合** — 固定 provider outcome 与 usage／response model／cost 的合法矩阵、PRIMARY-first reason、有限非负 Decimal、`CostUnavailable(USAGE_UNAVAILABLE)` 和历史 `NO_PRICING` restore 补算；B00 继续未授权实施，后由决策 303 关闭 scope taxonomy 与 context estimate 所有权。
301. **完成 B00 token usage 审查修订并同步核心文档** — 保留用户承担 context 配置／估算缓冲和 schema v3 单向兼容风险；新增显式 attempt scope、response envelope、OpenAI timeout 映射、严格 ledger invariant、整组可选费用与 `CostUnavailable(NO_PRICING)`，确认 pause 后继续追加并将验收扩为 16 项；后由决策 302 重开复审。
300. **完成 B00 token usage 方案并暂缓实施** — 固定交互式 Runtime attempt ledger、typed usage／outcome、schema v3、rewind、参考费用与计费单位、`/usage`、context preflight guard、MemoryExtractor 排除边界、精确实施白名单和初始 14 项验收矩阵；后由决策 301 完成审查修订，production／测试仍未授权。
299. **完成 B-01 无状态 SubAgent 生命周期修复并恢复全量测试环境隔离** — `cdb45e2`／`96fa690` 完成 fresh-start、closure-destroy、Plan／rewind、严格 schema v3 与旧 schema 隔离；用户 smoke 和 Codex 两轮审查关闭，CLI main 单测不再读取真实 `.env`，完整 unittest 356/356 通过，下一步回到 B00 方案讨论。
298. **完成 B-01 修复设计并授权下一新会话按白名单实施** — 使用 handoff `call_id` 标识 episode，增加 typed start／close signal，committed closure 后清空 target 与 Plan，Cancel／Paused 和 active snapshot 保留；schema 升 v3 并拒绝／隔离 v2，精确四个 production 文件、五个测试文件与验收矩阵已固定。
297. **恢复 SubAgent 单次 handoff 无状态契约并提升为 B-01** — 历史决策与用户确认均要求 SubAgent 仅在 active handoff 内保留多轮上下文，closure 后销毁并在下次 delegate 全新开始；当前 v2 跨 handoff 保留 history／plan 属于设计漂移，优先级高于 B00 token usage，当前只讨论方案。
