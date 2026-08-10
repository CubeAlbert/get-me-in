# 当前状态

**当前阶段：** B00 交互式 Runtime token usage 工程实现、两轮 review 修复与自动化验收已完成，正在等待真实 provider／估算校准验收；Interviewer production／测试实现仍未授权

**当前任务：** 按 [`docs/interviewer-agent-review.md`](interviewer-agent-review.md) B00 的精确 API／类型／序列化清单、2／16／2／11 文件白名单与 16 项验收完成工程实现和真实 provider 验收

**当前子任务：** 由用户运行 Main／Resume provider smoke，确认 response usage、实际 response model、`/usage` 增量及 save／restore，然后完成 estimator 与真实 input token 的校准记录。

**当前阻塞：** 当前没有技术硬阻塞；剩余真实 provider smoke 与 estimator 校准依赖用户的 provider／运行环境。Interviewer、context compression、Memory usage、cache-write、其他 provider 能力与白名单外 production／测试实现仍未授权。

**会话交接说明：** B-01 由 `cdb45e2` 实现并验证关闭。B00 初始实现已按白名单完成四个工程子任务提交；review 修复与补测提交为 `e66ff34`（handoff attempt 传播）、`d90ad21`（usage invariant／UI）、`5ac588b`（Runtime／provider／Session 验收覆盖）与 `04dadd6`（空 provider `choices` 仍保留 response model／usage）。当前完整 unittest `385/385`、`compileall` 与 `git diff --check` 通过；context 配置缺失时默认 `230000`／`0.95`，显式非法值仍拒绝。本机 `.env` 已按每百万 tokens 配置 CNY 参考价：FLASH uncached input／cached input／output 为 `1`／`0.02`／`2`，PRO 为 `3`／`0.025`／`6`；该部署配置不纳入 Git。真实 provider smoke 与 estimator calibration 尚未执行。

**下一步：** 用户运行 Main／Resume 真实 provider smoke 并记录 `/usage`、save／restore 结果，再用代表性请求校准 estimator；任何必须扩大文件、API、schema、依赖或数据边界的情况立即停止并重新授权；B00 验收关闭后再恢复 B03 Review。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

310. **关闭 B00 最终代码复审并配置本机参考价格** — 修复空 provider `choices` 丢失 response metadata，确认只记录 cached input、output 使用统一价格；完整测试增至 385 项，并在本机 `.env` 配置 FLASH／PRO CNY 参考价，真实 provider smoke 与 estimator calibration 仍为下一门禁。
309. **修复 B00 review findings 并补齐工程验收覆盖** — 修复 handoff failure attempt 传播、cached basis invariant 与 `/usage` 信息丢失，新增 Runtime／provider／Session 生命周期补测；完整测试增至 383 项，真实 provider smoke 与 estimator calibration 仍为下一门禁。
308. **完成 B00 工程实现 checkpoint** — 按 2／16／2／11 白名单拆分四个代码提交，373 项测试、compileall 与 diff-check 通过；真实 provider smoke 与 estimator calibration 保留为下一验收门禁，Interviewer 与白名单外实现仍未授权。
307. **授权下一新会话实施 B00 token usage** — 最终就绪审计确认当前调用点、SDK、schema、2／16／2／11 白名单和 16 项验收可落地；用户授权下一新会话按清单 coding，当前会话只更新并提交文档，Interviewer 与白名单外实现仍未授权。
306. **补齐 B00 精确 API、类型与 schema v3 序列化清单** — 固定 module/type/field/enum、构造依赖、public query、transition propagation、Settings／CLI surface、`llm_attempts` exact key set 与 usage／cost tagged unions；新会话可直接按清单实施，但 coding 仍未授权。
305. **关闭 B00 第二轮复审并恢复暂缓实施状态** — 最终验证 decision TOC／正文、current 最近 10 条、白名单 2／16／2／11、16 项验收、active 文档术语与 diff-check 一致；B00 恢复“已决定（暂不实施）”，下一步回到 B03。
304. **删除 B00 cache-write 并关闭 replay／identity 语义** — 首版只保留 input／cached input／output 计价，固定 `REPORTED_BREAKDOWN`／`ASSUMED_UNCACHED`；相同 record replay no-op、冲突拒绝、codec duplicate 拒绝，identity 非空、timestamp 带时区且最近记录按 append order 获取。
303. **固定 B00 最小 scope taxonomy 与 context estimate 单一路径** — 删除冗余 component，固定必填 Agent／turn、可选 handoff episode 与 `RUNTIME_DECISION` purpose；preflight 和只读 `/usage` estimate 复用 Runtime 唯一 request builder，并固定公开 Application→SessionService→Orchestrator→Runtime 查询链。
302. **重开 B00 复审并补强 attempt／usage／cost 合法组合** — 固定 provider outcome 与 usage／response model／cost 的合法矩阵、PRIMARY-first reason、有限非负 Decimal、`CostUnavailable(USAGE_UNAVAILABLE)` 和历史 `NO_PRICING` restore 补算；B00 继续未授权实施，后由决策 303 关闭 scope taxonomy 与 context estimate 所有权。
301. **完成 B00 token usage 审查修订并同步核心文档** — 保留用户承担 context 配置／估算缓冲和 schema v3 单向兼容风险；新增显式 attempt scope、response envelope、OpenAI timeout 映射、严格 ledger invariant、整组可选费用与 `CostUnavailable(NO_PRICING)`，确认 pause 后继续追加并将验收扩为 16 项；后由决策 302 重开复审。
