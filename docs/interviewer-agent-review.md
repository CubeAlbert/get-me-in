# R9 InterviewerAgent 前置 Review 与阻塞点追踪

> 状态：R9-P 前置 Review 进行中
> 分支：`feat/interviewer-agent`
> 首次审查日期：2026-08-05
> 授权边界：B-01 已实现并验证关闭；Interviewer、B00 及其他 production／测试实现仍未授权
> canonical 命名：新能力统一为 `InterviewerAgent`／`AgentKey.INTERVIEWER`；既有文档中的 `InterviewAgent` 原文不回写

## 1. 文档用途

本文是 R9 InterviewerAgent 的当前专项 Review 入口，用于逐条讨论、记录和关闭 coding 前阻塞点。每个阻塞点都保留：

- 当前代码事实与为什么会阻塞；
- 必须回答的问题；
- 可选方案与推荐方向；
- 用户确认后的最终决策；
- 可验证的关闭条件。

本文件不是实现授权，也不是最终 API 清单。全部阻塞点关闭后，仍须先形成精确文件／类／公开方法白名单、实施切片和验收矩阵，再由用户单独授权 coding。

## 2. 已确认、不再作为开放阻塞点的边界

以下结论由当前架构和既有 R9 备忘共同固定，除非用户明确重开：

1. InterviewerAgent 是 Hub-and-Spoke 中的一个 spoke；Main 继续是唯一跨 Agent 调度中心。
2. Workflow 是 InterviewerAgent 内部执行策略；workflow node 不是子 Agent，不能直接 handoff 到其他子 Agent。
3. 采用“确定性 Workflow 外壳 + 节点内 LLM”，不用提示文本或模型自由决定整体控制流。
4. 不引入 LangChain、LangGraph、CrewAI、AutoGen 或异步框架；若要引入，必须另立架构与依赖决策。
5. `SessionState` 继续是全部长期运行状态的唯一 canonical owner；executor/runtime 不保存第二份长期状态。
6. 工具和外部副作用继续经过 capability、port、application service 与 typed outcome；workflow node 不直接访问 CLI、SDK、文件系统或全局对象。
7. 四个 legacy 用户数据目录继续禁止读取、改写、迁移或删除：`data/save/`、`data/memories/`、`data/chroma/`、`data/temp/`。
8. 本轮先完成 Review；在精确实现清单和用户 coding 授权前，不创建生产类、schema migration、配置或测试实现。

## 3. 阻塞点总表

状态说明：`待讨论` → `讨论中` → `已决定` → `已验证关闭`。`已决定` 只表示设计已确认，不表示允许 coding。

| ID | 阻塞点 | 当前状态 | 主要依赖 | 阻塞的下一步 |
|---|---|---|---|---|
| B-01 | SubAgent 单次 handoff 上下文生命周期与退出销毁 | 已验证关闭 | 当前 Session／handoff 链路 | 已解除 |
| B00 | 逐次 LLM token usage 的采集、归属、持久化与查询 | 讨论中 | B-01、当前 LLM／Session 链路 | 后续 Workflow 预算与实施 |
| B01 | MVP 产品职责、命名、输入与完成条件 | 已验证关闭 | 无 | 全部后续设计 |
| B02 | Workflow 阶段、分支、循环与预算上限 | 已验证关闭 | B01 | state、executor、测试 |
| B03 | typed executor protocol 与 agent-local state 形状 | 待讨论 | B02 | Orchestrator、Session、composition |
| B04 | 每问一答的 `RuntimeCommand`／`RuntimeEvent` 语义 | 待讨论 | B02、B03 | CLI drive、finalize、snapshot |
| B05 | Session snapshot schema 与 v3→Interviewer schema 兼容 | 待讨论 | B03、B04、B-01 | save／restore |
| B06 | Interview 回合的 rewind 与稳定恢复点 | 待讨论 | B02、B03、B05 | `/rewind`、副作用安全 |
| B07 | 暂停、Esc 取消、停止面试、`/exit_sub` 与 handoff closure | 待讨论 | B02～B04 | 生命周期与退出 |
| B08 | 回答、评分、进度、最终报告的数据所有权 | 待讨论 | B01、B02 | domain／repository 边界 |
| B09 | 隐私、日志、auto-memory、删除入口与 retention | 待讨论 | B08 | 持久化和真实使用 |
| B10 | question／rubric／JD 输入来源与版本化 | 待讨论 | B01、B02 | 问题生成与评分可复现性 |
| B11 | AgentSpec、capability、配置与 composition root 清单 | 待讨论 | B01～B10 | 精确 production 白名单 |
| B12 | 实施切片、回归矩阵、真实 smoke 与停止门禁 | 待讨论 | B01～B11 | coding 授权 |

当前讨论顺序：

```text
B-01（已验证关闭）
  ↓
B00（全局 token usage 与 context guard）

B01（已关闭）
 ├─→ B02 ─→ B03 ─→ B04 ─→ B05 ─→ B06
 │                    └────────────→ B07
 ├─→ B08 ─→ B09
 └─→ B10

B01～B10 ─→ B11 ─→ B12 ─→ 单独 coding 授权
```

## 4. 阻塞点详情

### B-01 —— SubAgent 单次 handoff 上下文生命周期与退出销毁

**当前状态与授权**

- 用户确认原始 v1 契约是：SubAgent 只在一次 active handoff 内保留多轮上下文；退出后销毁该 SubAgent 上下文，下次调用从全新状态开始。
- 用户要求本项优先级高于 B00 token usage，并明确旧 snapshot 可以放弃、不要求向前兼容。
- 用户随后授权并完成精确白名单内实现；`cdb45e2` 落地生命周期／Plan／rewind／schema v3，`96fa690` 关闭严格 schema 审查 finding，当前状态为“已验证关闭”。

**历史契约证据**

- 决策 51 明确写明“子 Agent 无状态，不持有任何持久上下文”。
- 决策 78 再次固定：Main 只保留异步 tool call 与返回 summary，子 Agent 多轮交互不进入 Main history，且“子 Agent 无持久状态”。
- 后续 Plan 决策也要求子 Agent plan 随 return 丢弃，以保持无状态原则。

**实现结果**

- Main→Sub 现在从 canonical 空 `AgentSessionState()` 启动；正常 return、主动退出和真实 failure closure 后清空 target，Cancel／Paused 继续保留 active episode。
- `SessionTransition.started_agent`／`closed_agent` 驱动 SessionService 清理 PlanService；restore 只恢复 active Agent plan，通用 Main rewind 清空全部 SubAgent state／plan。
- snapshot baseline 已升为严格 v3；v2 显式拒绝且 list 隔离，malformed v3 不会被静默隐藏，v3 必填 `turn_id` 不再执行 legacy 回填。
- 用户确认 Windows smoke 已完成；Codex 两轮代码审查关闭全部 finding，B-01 定向、完整 unittest、compileall、diff-check 与 import-boundary 均通过。

**已确认的目标不变量**

- 每次 Main→Sub handoff 创建一个全新的 SubAgent episode；首次模型输入只包含该 Agent system prompt 与本次 delegate context，不包含以前 episode 的 history／plan／pending state。
- active handoff 内允许 SubAgent 跨多个用户回合保留上下文；只有 handoff 仍活动时，取消／暂停后的下一条用户输入才继续原 SubAgent episode。
- handoff 正常 return、用户明确退出、放弃或 failure closure 后，销毁该 episode 的 SubAgent 对话与 agent-local workflow／plan state；Main 只保留原 tool call 的 typed return／failure summary。
- 销毁 SubAgent context 不回滚 Session 顶层的真实 LLM token usage；下次新 episode 产生的新调用继续累加到同一 Session 全局 usage。
- Session save 发生在 active handoff 时，必须能够恢复该 active episode；handoff 已闭合后再 save，不得把已销毁的 SubAgent episode 作为可继续上下文恢复。

**最终设计（已确认）**

1. **Episode identity 与 fresh start**
   - 不新增独立 `episode_id` 类型；复用 Main→Sub handoff frame 的唯一 `call_id` 作为 episode identity，供后续 B00 usage record 关联。
   - `_start_subagent` 必须以新的 `AgentSessionState()` 推进 target `UserMessage(delegate_context)`，不得把 `session.agents[target]` 的旧 state 传入 Runtime。
   - target key 继续存在于 `SessionState.agents`；“无状态”表示非活动 SubAgent 的 value 必须等于 canonical 空 state，不表示从 composition 删除 Agent。

2. **Typed lifecycle signal**
   - 现有 `SessionTransition` 增加 `started_agent: AgentKey | None = None` 与 `closed_agent: AgentKey | None = None`；不得通过 event message、active-agent 差值或裸 dict 猜测生命周期。
   - Main→Sub 成功时只设置 `started_agent=target`；所有 committed closure 只设置 `closed_agent=target`；同一 transition 不得同时 start 与 close。
   - `SessionService` 根据 typed signal 清空对应 `PlanService`，避免现有逻辑在 Orchestrator 已清空 target state 后又把旧 plan snapshot 写回。

3. **Closure commit 顺序**
   - 正常 return／partial return：Sub 已生成 typed summary → Main Runtime 用原 `call_id` 执行 `CompleteHandoff` → Main closure state 成功形成 → pop frame、切回 Main、target 重置为 `AgentSessionState()` → 返回 `closed_agent`。
   - `/exit_sub summarize=false`／abandon：Main 用原 `call_id` 执行 `FailHandoff` → closure commit → target 重置为空。
   - SubAgent 真实 `Failed`：Main 用 terminal `FailHandoff` 记录 typed failure → closure commit → target 重置为空；Main 保留 failure 事实，Sub transcript 不保留。
   - 若 Main closure command 抛异常或未形成合法 closure state，不得清空 target 或弹出 frame；原 active episode 保持可诊断状态。

4. **保留与销毁矩阵**

   | 路径 | handoff | target state |
   |---|---|---|
   | 正常／partial return | 闭合 | 清空 |
   | `/exit_sub` summarize／abandon 完成 | 闭合 | 清空 |
   | 真实 SubAgent failure closure | 闭合 | 清空 |
   | Esc／Ctrl+C `Cancelled` | 保留 | 保留 active episode |
   | 可恢复 `Paused`／选择取消 | 保留 | 保留 active episode |
   | active handoff 时 save／dump | 保留并可 restore | 保存 active target state |
   | closed handoff 后 save／dump | 已闭合 | 所有 SubAgent 均为空 |

5. **Plan、rewind 与其他副作用**
   - start／closure 时同步把 target `PlanService.restore(None)`；restore 新 Session 时先清空全部 PlanService，再只恢复 active Agent 的 plan。
   - 当前通用 `/rewind` 只提供 Main turn point；执行后切回 Main、清空 handoff，并把所有 SubAgent state／plan 重置为空。未来 Interviewer episode 内 rewind 仍由 B06 单独设计。
   - B-01 只销毁 Agent context／plan／pending／turn-local/workflow state；不撤销已提交 Workspace 文件、Artifact、Memory、Knowledge 或其他外部副作用。
   - `WorkspaceAccessState` 当前按 `(session_id, path)` 而不是 Agent 保存，是 Session 共享授权；B-01 不修改或清除该状态，避免误伤 Main。restore／rewind 继续沿用现有 session 级清理。

6. **Snapshot v3 与旧文件策略**
   - `SCHEMA_VERSION` 从 2 升到 3；codec 只 encode／decode v3，不提供 v2 migration、upgrade 或 fallback。
   - v3 invariant：无 active handoff 时全部非 Main state 必须为空；有 active handoff 时只有 frame.target 可以非空，其他非 Main state 必须为空。
   - v2 文件不读取为 Session、不自动改写、不迁移、不删除；显式 restore 返回 typed `UnsupportedSessionSchemaError`。
   - `JsonSessionRepository.list()` 只跳过 `UnsupportedSessionSchemaError` 对应的旧 schema 文件，使旧文件不阻塞新 Session 列表；损坏的当前 v3 文件仍必须报错，不能静默隐藏。
   - B00 可在 v3 顶层增加向后兼容的可选 Session usage ledger；B05 的 Interviewer typed state 后续以 v3→v4 重新讨论，不再假设 v2→v3。

**精确 production 白名单（下一会话已授权范围）**

| 文件 | 允许修改 |
|---|---|
| `src/get_me_in/application/orchestration.py` | 扩展 `SessionTransition` typed lifecycle signal；fresh start；normal／exit／failure closure 后清空 target |
| `src/get_me_in/application/session_service.py` | 统一提交 lifecycle transition；start／close／restore／rewind 的 PlanService 与 SubAgent state 协调 |
| `src/get_me_in/application/session_codec.py` | schema v3、`UnsupportedSessionSchemaError`、inactive SubAgent empty invariant |
| `src/get_me_in/adapters/json_session_repository.py` | list 跳过明确 unsupported schema；load 继续显式报错且不改写文件 |

允许新增／修改的公开契约仅为：

- `SessionTransition.started_agent: AgentKey | None`
- `SessionTransition.closed_agent: AgentKey | None`
- `UnsupportedSessionSchemaError(ValueError)`

不得新增 production 文件、公开方法、配置、Prompt、依赖或数据迁移；不得修改 `WorkspaceAccessState`、Artifact／Memory／Knowledge、CLI 命令或四个 legacy 数据目录。

**精确测试白名单与验收矩阵**

| 文件 | 必须覆盖 |
|---|---|
| `tests/get_me_in/test_orchestration.py` | fresh target、normal／exit／failure 清空、cancel／pause 保留、Main summary／call id 不变 |
| `tests/get_me_in/test_sessions.py` | PlanService start／close／restore 清空、rewind 清空全部 SubAgent、active episode save 语义 |
| `tests/get_me_in/test_session_codec.py` | v3 round-trip、v2 拒绝、inactive non-empty 拒绝、active target 保留、其他 SubAgent 必须为空 |
| `tests/get_me_in/test_json_session_repository.py` | list 跳过 v2、load v2 显式失败、旧文件仍存在、损坏 v3 仍报错 |
| `tests/get_me_in/test_bootstrap.py` | Main→Resume→Main 后 Resume 为空；第二次 handoff 无旧 history；active save／restore 可继续 |

工程门禁：先运行上述定向测试，再运行完整 `unittest`、`compileall`、`git diff --check` 和 import-boundary 回归。真实 Windows TTY smoke 至少覆盖：正常 return 后再次进入 Resume 为全新上下文、active SubAgent Esc 后继续仍保留上下文、active save／restore 可继续、closed save／restore 后重新进入为空。

**关闭条件**

- ✅ lifecycle、fresh start、closure 顺序、cancel／pause、Plan、rewind、side-effect 边界、schema v3 和旧 snapshot 策略均已固定。
- ✅ production／测试／公开契约白名单与自动化／TTY 验收矩阵完整。
- ✅ 已按白名单实施；用户 smoke、两轮代码审查、定向／完整自动化、compileall、diff-check 与 import-boundary 均已完成，状态为“已验证关闭”。

### B00 —— 逐次 LLM token usage 的采集、归属、持久化与查询

**当前状态与授权**

- 用户在确认 B02 后提出：当前系统没有统计会话中的 token 用量，必须支持获取每一次 LLM 调用的 token 消耗。
- B-01 已验证关闭，本项恢复为当前最高优先级；当前只授权审计和方案设计，不授权 production／测试实现。

**当前代码事实**

- `LLMResult` 当前只返回 `content`；`OpenAILLMAdapter` 没有读取 Chat Completions response 的 `usage`。
- 当前锁定的 OpenAI SDK `2.43.0` 对 Chat Completions 提供 `prompt_tokens`、`completion_tokens`、`total_tokens`，并可选提供 `cached_tokens`、`reasoning_tokens` 等细分字段。
- `AgentRuntime` 在 provider 调用前递增 `model_calls`，但该计数只表达当前用户回合的调用次数；新 `UserMessage` 会重建 per-turn state，因此它不是跨回合 token ledger。
- `SessionView` 与 CLI `/status` 当前不包含 token 用量；B-01 已把 snapshot baseline 升为 schema v3，但 v3 初始仍没有逐次 LLM usage 记录。
- 除 Main／Resume Runtime 外，MemoryExtractor 也直接调用 `LLMPort`；OpenAI Web Search 与 embedding 等 provider 请求不经过同一 `LLMPort`，是否纳入首版统计必须明确。
- provider failure、timeout 或 cancellation 可能已经产生计费 token，但通常拿不到可靠 `usage`；不能用 `0` 冒充未知。

**必须讨论**

1. 首版范围是只统计交互式 Agent Runtime，还是覆盖所有 `LLMPort.complete()`（含 MemoryExtractor）；Web Search、embedding、未来 STT／TTS 是否明确排除。
2. canonical 字段：input／output／total 是否足够；是否同时保留 cached input、reasoning output、model、agent、turn、调用目的和结果状态。
3. “每次调用”按逻辑节点还是每次 provider attempt 记录；格式修复、恢复重试、失败、超时和取消如何表达。
4. 已确认的 Session 顶层 ledger 如何与 Runtime／MemoryExtractor 的 typed result 汇合；不得退回 agent-local state、独立 repository 或短暂日志。
5. B00 是否在 schema v3 顶层增加向后兼容的可选 usage ledger；restore、dump、session 删除与 retention 如何处理。
6. 查询入口：公开 Application API、`SessionView`／`/status`、独立 `/usage` 命令或组合；需要逐次明细、按 Agent／turn 汇总还是两者都要。
7. provider 不返回 usage 时使用何种 typed unknown 状态；是否允许本地 tokenizer 估算，以及估算值能否参与预算／成本判断。
8. fake LLM、OpenAI-compatible provider 与真实 provider smoke 的验收矩阵。

**初步推荐方向（待确认）**

- 在 provider-neutral contract 中区分“调用记录”和“已知 token usage”；成功但无 usage、失败、超时、取消均保留 attempt，usage 为明确 unavailable，不记为 0。
- 最小稳定计数使用 input／output／total；cached／reasoning 作为可选细分字段。记录实际 model、Agent、turn、purpose 和 outcome，以便未来 Interviewer 按 node 做预算。
- 按每次 provider attempt 记录，格式修复与恢复重试各是一条独立记录；逻辑调用可通过稳定 logical call id 聚合。
- 已发生的计费事实不随 rewind 删除。若统计用于 Session 预算，canonical ledger 应由 `SessionState` 或与其有明确一致性契约的 owner 持有，不能只写日志。
- 首版优先覆盖所有 `LLMPort.complete()`；Web Search、embedding、STT／TTS 属于不同 usage 类型，明确排除并留待独立扩展。
- 提供独立只读 `/usage` 入口，默认展示当前 Session 汇总和最近调用；公开 Application API 返回强类型数据，CLI 不读取 Runtime 私有字段。
- 不使用本地 tokenizer 伪装 provider 账单数字；缺失 usage 保持 unknown。若未来需要估算，必须使用独立 `estimated` 标志和口径。

**已确认的设计**

- 所有 `LLMPort.complete()` provider attempt 均进入 `SessionState` 顶层全局 ledger，至少覆盖 Main、Resume、MemoryExtractor 和未来 Interviewer；Web Search、embedding、STT／TTS 首版排除。
- ledger 按 actual attempt 记录，并以 logical call id 聚合重试／格式修复；provider 未返回 usage 时保留 typed unknown，不记 0，不用本地 tokenizer 冒充账单数字。
- `/rewind` 不回滚已经发生的 Session lifetime usage，也不单独展示“rewound usage”；它只回退模型可见 history，并重新计算当前 context estimate。销毁 B-01 SubAgent episode 同样不回滚全局 usage。
- 独立 `/usage` 展示当前 Session lifetime 汇总、按 Agent／component 明细、unknown attempt 和最近逐次记录；不把完整 ledger 塞进 `/status`，CLI 只经公开 Application query。
- context safety 与累计 usage 分离：每个 Agent／每次请求有独立 context window；预留 `context_window_tokens`、`compression_threshold_ratio=0.95`、`reserved_output_tokens`、`ContextSizer` 与 `ContextPolicy`。
- provider usage 是调用后的真实计量，不能单独承担防爆保护；未来必须在调用前估算 system prompt、tools、history、handoff、当前输入和输出预留。自动压缩未实现前达到阈值必须 fail-closed 进入 typed pause，禁止冒险请求。
- 未来压缩只替换模型可见工作上下文为“摘要 + 最近记录”，不删除累计 usage；原始 transcript 与模型可见上下文是否正式拆成两个持久化层仍待 B00 后续确认。

**最终决策状态**

> 核心 owner、rewind、全局汇总与 context guard 已确认；B-01 已关闭，下一步继续确认数据类型、写入时序、transcript／working-context 分层、schema v3 可选字段和精确实现白名单。

**关闭条件**

- 统计范围、字段、attempt／logical call identity、owner、snapshot 兼容、rewind、查询入口、unknown 语义和验证矩阵全部确认。
- 形成精确文件／类／公开方法白名单，并由用户另行授权后才可实现。

### B01 —— MVP 产品职责、命名、输入与完成条件

**审查起点**

- 当前 production Catalog 只有 Main 与 Resume；历史 `InterviewAgent` 只是 R9 备忘，不是已确认产品契约。
- 分支已采用 `feat/interviewer-agent`，但当前文档、`AgentKey` 候选和历史设计仍使用 `InterviewAgent`。
- B01 讨论前尚未确认首版面试类型、用户必须提供的上下文、输出内容、何时算完成，以及明确不做什么。

**必须讨论**

1. 新能力的 canonical 名称是否统一为 `InterviewerAgent`／`AgentKey.INTERVIEWER`，历史记录继续保留 `InterviewAgent` 原文。
2. 首版支持技术面、行为面、项目深挖、系统设计还是混合模式；是否只选一种模式作为第一个纵向切片。
3. 启动所需最小输入：目标岗位、级别、JD、简历／经历、语言、期望时长，哪些必填、哪些可选。
4. 是否逐题即时反馈，还是只在结束时给总评；最终输出至少包含哪些字段。
5. 完成条件：固定题数、时间预算、用户主动结束、评分达成，或它们的组合。
6. 首版非目标：语音、视频、实时 coding sandbox、公司题库抓取、多面试官、多会话并行等是否明确排除。

**讨论时推荐方向（已由最终决策取代）**

- 新代码统一使用 `InterviewerAgent` 与 `AgentKey.INTERVIEWER`；历史决策不改写。
- 第一个纵向切片只做“基于目标岗位／可选 JD 的单场文本模拟面试”：准备 → 多轮问答 → 总结报告 → 返回 Main。
- 支持一种明确的 MVP 模式，其他模式只作为后续扩展；不在首片同时引入语音、coding sandbox、外部题库抓取或多会话。
- 逐题内部评分用于分支与最终报告，是否向用户即时展示单独决定，避免反馈改变后续回答。

**最终决策**

- canonical 产品名称统一为 `InterviewerAgent`，稳定枚举为 `AgentKey.INTERVIEWER`；沿用现有声明式 Agent 风格，是否需要具体实现类及其类名留到 B03／B11 决定，既有历史决策中的 `InterviewAgent` 原文不回写。
- MVP 只做基于用户提供 JD 与简历摘要的单场文本岗位技术模拟面试，固定主流程为：Main 转交 → 确认输入 → LLM 准备问题 → 多轮问答与判断 → 统一生成报告 → 返回 Main。
- MVP 不依赖外部 tool call；`query_reference_data`、`query_memory` 及其他检索能力均不开放。问题由 Interviewer LLM 生成，回答暂由同一 Interviewer LLM 判断；同一上下文评分的提示词注入与上下文污染风险作为已接受的首版限制。
- 启动前必须由 Interviewer 显式询问并取得用户提供的 JD 与简历摘要，不得自动从 Memory、Knowledge、Resume workspace 或历史会话读取。语言沿用当前 resolved response locale，题数默认 5；MVP 不支持通过自然语言修改二者，未来如开放选择，必须由 typed state／command 驱动，而不是让 LLM 识别设置语义。
- 面试过程中不向用户展示逐题评分或即时反馈；结束后统一展示报告。未来可单独设计 Observer Agent 对每题隔离评分，但不属于 MVP，也不构成当前架构或实现授权。
- 正常完成默认题数后生成完整报告；用户可主动提前结束并生成明确标注为 partial 的部分报告。必须提供可发现的指定命令并使用 typed lifecycle 语义，精确命令、状态转换与 handoff closure 转交 B07。
- MVP 不实现计时或时间预算终止。B11 只评审可替换计时模块的接口边界，不实现时钟策略；未来必须区分模型生成、TTS 播放、用户听取／阅读、STT 和用户作答时间，不能简单从模型输出完成时开始扣减统一答题时限。
- 最终报告使用稳定、带版本的模板填充，不允许每次自由改变结构；模板至少表达面试目标与完成度、总体及分维度评价、逐题证据、优势、短板／风险和改进建议。精确 schema、owner、渲染与持久化边界转交 B08／B10。
- MVP 明确排除：语音、视频、STT／TTS、实时 coding sandbox、外部题库／Reference／Memory 检索、多面试官、Observer Agent、多会话并行、运行时语言／题数自然语言配置以及计时执行。

**关闭条件**

- ✅ canonical 命名、首版职责、启动输入、默认语言／题数、反馈时点、完成与 partial 退出、模板化用户输出和非目标均已明确。
- ✅ 尚未细化的 typed 退出命令、报告 schema／owner、LLM question／rubric 约束和计时接口已分别路由至 B07、B08、B10、B11，不阻塞关闭产品范围。

### B02 —— Workflow 阶段、分支、循环与预算上限

**当前事实**

- 现有 `AgentRuntime` 是 ReAct 形状；一个 `UserMessage` 开始一次 run，模型与工具可循环，`Completed` 结束当前 run。
- Interviewer workflow 需要跨多个用户回合保留题目、回答、评分和追问进度；不能依赖模型自由选择下一阶段。
- 当前只有通用 `AGENT_MAX_MODEL_CALLS`，没有题数、追问数、整场面试调用数或 workflow retry 上限。

**必须讨论**

1. 稳定 stage／step 列表以及允许的 transition。
2. 问题数量、每题最大追问、整场最大追问、模型调用、格式修复和 provider failure retry 上限。
3. 低质量／空泛回答、用户拒答、跑题、要求提示、修改上一答案分别如何转移。
4. 评分是在每题后一次完成，还是允许“评估 → 追问 → 再评估”；最终分数如何聚合。
5. 用户主动结束时是生成部分报告，还是直接退出不评分。

**推荐方向（待确认）**

```text
RECEIVED_HANDOFF
  → AWAITING_CONFIRMATION
  → PREPARING
  → ASKING
  → AWAITING_ANSWER
  → EVALUATING
  → ASKING_FOLLOWUP | ASKING_NEXT | SUMMARIZING
  → RETURNING_TO_MAIN
  → COMPLETED
```

- transition 使用纯函数或等价的确定性 domain 逻辑；LLM node 只返回强类型结果。
- 所有循环都有配置化硬上限；达到上限时走可解释的总结／失败路径，不继续隐式调用。
- snapshot 只落在 `AWAITING_CONFIRMATION`、`AWAITING_ANSWER`、可恢复失败和完成等稳定点。

**最终决策**

- 稳定阶段固定为：`RECEIVED_HANDOFF` → `COLLECTING_CONTEXT` → `AWAITING_START_CONFIRMATION` → `PREPARING` → `ASKING` → `AWAITING_ANSWER` → `EVALUATING` → `ASKING_FOLLOWUP | ASKING_NEXT | SUMMARIZING` → `RETURNING_TO_MAIN` → `COMPLETED`。
- `COLLECTING_CONTEXT` 取得 B01 要求的 JD 与简历摘要；确认页展示输入摘要、resolved response locale 和默认 5 道主问题，只有用户确认后才进入 `PREPARING`。
- 每道主问题最多追问 1 次，整场最多追问 3 次；追问不计入默认 5 道主问题。LLM 只能返回追问建议，是否仍有额度并实际转移由确定性状态机决定。
- 正常回答进入隐藏评估；空泛／信息不足或明显跑题在有额度时追问一次，否则记录“证据不足”并进入下一题；空输入不调用 LLM；明确拒答记录“用户跳过”并进入下一题。
- 用户可请求一次提示，后续回答标记为“获得提示”，且提示占用该题唯一一次追问额度。MVP 不通过自然语言修改上一题答案，回退语义交由 B06。
- 每次回答后由同一 Interviewer LLM 返回强类型判断，至少区分 `ACCEPT_AND_NEXT`、`ASK_FOLLOWUP`、`INSUFFICIENT_AND_NEXT`；状态机校验计数后决定实际分支。若发生追问，该题最终评价综合原回答和追问回答。
- 未回答、拒答或证据不足不直接计为零分；partial 报告只基于已完成评估的问题，并显式展示完成度。MVP 不因达到某个分数而提前结束，精确 rubric 与聚合公式交由 B10。
- 每场最多 10 次逻辑 LLM 调用：准备 1 次、最多 8 次回答评估、报告 1 次；每次逻辑调用最多 1 次格式修复，整场最多 20 次实际模型请求。provider／transport error 不在 Workflow 内静默循环，转入可恢复路径，精确 pause／resume 由 B07 决定。
- partial 结束从稳定的用户等待点进入 `SUMMARIZING`：已评估回答进入报告，当前未回答问题标记为未完成，不再生成新问题；报告生成后正常返回 Main，不按 failure 处理。
- B00 将补充逐次 LLM token usage 的统计口径；在 B00 关闭前不把 token 数作为本 Workflow 的控制预算，也不改变本条已确认的调用次数硬上限。

**关闭条件**

- ✅ stage、transition、异常回答分支、提示／拒答语义、追问与模型调用上限、隐藏评估、partial 总结路径均已固定。
- ✅ token usage 统计已独立提升为 B00；它不阻塞 B02 产品与 Workflow 控制流结论，但在 B00 关闭前不得据 token 数实现新预算。

### B03 —— typed executor protocol 与 agent-local state 形状

**当前事实**

- `Orchestrator` 当前直接依赖 `Mapping[AgentKey, AgentRuntime]`。
- `AgentRuntime.advance()` 固定接收并返回 `AgentSessionState`；`RuntimeTransition.state` 也是该具体类型。
- `AgentSessionState` 直接包含 ReAct `RuntimePhase`、conversation history、pending tool、repair counter 和 Plan，无法类型安全地表达 Interview workflow version、step、question、answers、evaluations 和 termination reason。
- `SessionService`、snapshot codec、rewind 和 Plan restore 都假定所有 Agent 使用相同 ReAct state。

**必须讨论**

1. 是否引入最小 `AgentExecutor` Protocol；其 `advance`、`request_cancel`、`close` 的精确签名。
2. Session 中使用 tagged union，还是使用包含 common header + typed payload 的 envelope。
3. ReAct 与 Interview state 真正共享哪些字段；不能为了复用而把 Interview 数据塞进 `Plan` 或开放 `metadata`。
4. `SessionView.phase` 如何投影不同 executor 的状态，CLI 是否只需要统一的高层 phase。
5. `PlanService` 是否仍为 InterviewerAgent 必需依赖；若不用，`SessionService` 不能继续假定每个 Agent 必有 Plan。

**推荐方向（待确认）**

- 引入最小、同步、无状态副本的 `AgentExecutor` Protocol；Orchestrator 只依赖该协议。
- Session agent-local state 使用显式 tagged union，而不是开放 dict；ReAct state 保持强类型，新增 versioned `InterviewerWorkflowState`。
- executor transition 返回对应的 typed state union 和既有 `RuntimeEvent`；长期状态只由 `SessionService` 接收并写回 `SessionState`。
- common state 只放真正跨 executor 共用的 identity／history／用户回合投影；workflow-specific 字段留在 Interviewer payload。

**最终决策**

> 待讨论。

**关闭条件**

- Protocol、state union/envelope、transition、view projection 和 Plan 可选性都有精确类型草案；未留下 `object`／开放 metadata 逃生口。

### B04 —— 每问一答的 RuntimeCommand／RuntimeEvent 语义

**当前事实**

- CLI 遇到 `Progress`、`ToolStarted`、`ToolFinished`、`HandoffRequested` 会自动发送 `Continue`。
- CLI 遇到 `Completed`、`Failed`、`Paused`、`Cancelled` 会停止内层 drive，并立即调用 `finalize_turn()` 保存 snapshot，且可能触发 auto-memory。
- `Completed` 在当前系统实际表示“当前用户 run 完成”，不是“整个 Agent 生命周期永久结束”；下一条 `UserMessage` 可以再次启动。
- 面试提问需要“本回合向用户输出问题并停止 drive，但 workflow 仍处于等待回答状态”。

**必须讨论**

1. 复用 `Completed` 作为 turn-terminal 事件，还是新增 `AwaitingUserInput`。
2. 问题、追问、确认和最终报告分别用何种事件输出；CLI 是否需要知道它们的业务类型。
3. 哪些 terminal event 触发 snapshot、auto-memory 和用户输入 prompt。
4. `UserMessage` 在 `AWAITING_CONFIRMATION`、`AWAITING_ANSWER`、可恢复失败等 stage 中的 typed 解释。

**推荐方向（待确认）**

- 优先复用 `Completed` 的“用户回合已完成”语义，由 typed workflow state 表达 `AWAITING_ANSWER`，不为了展示一条问题就扩展公共 event。
- 只有当 CLI 必须对“等待答案”提供不同于普通完成的行为时，才增加最小新事件；不得靠 message 文本匹配。
- 无论选哪种方案，必须把 snapshot 与 auto-memory 分开决策，不能继续把所有 terminal event 视为相同数据策略。

**最终决策**

> 待讨论。

**关闭条件**

- command/event transition table 能覆盖确认、问题、回答、追问、报告、可恢复错误和结束；CLI 不需要猜测 workflow stage。

### B05 —— Session snapshot schema 与 v3→Interviewer schema 兼容

**当前事实**

- 当前代码只接受并写出严格的 `schema_version=3`；B-01 已明确拒绝 v2，且 malformed v3 必须显式报错。
- B-01 v3 仍使用单一 ReAct `AgentSessionState` 形状，只新增 inactive SubAgent empty invariant；没有 state kind/tag。
- restore 会拒绝 snapshot 中存在但当前 composition 未装配的 Agent。
- 当前运行数据属于 `data/runtime/`，不是 legacy 目录；本 Review 不读取其中的用户数据。

**必须讨论**

1. Interviewer typed state 是否把 schema 从 B-01 v3 升为 v4；是否在 v4 中给每个 agent-local state 增加稳定 tag 与独立 version。
2. v3 snapshot 的支持策略：decode-and-upgrade、只读兼容或显式拒绝；v2 已由 B-01 明确不兼容，不再重开。
3. 含 Interviewer state 的 snapshot 在未装配 InterviewerAgent 的版本中如何报错。
4. 哪些 workflow stage 可持久化；进行中的 LLM／评估／副作用 stage 如何 normalise。
5. migration 的原子性、失败回退和测试 fixture。

**推荐方向（待确认）**

- bump 到 session schema v4；v4 agent state 使用显式 `kind` + state schema version。
- codec 继续接受 B-01 v3，并确定性升级为 v4 ReAct state；encode 只写 v4。v2 继续拒绝，四个 legacy 目录继续不读取／改写。
- 只允许稳定 workflow stage 被直接保存；不稳定 stage 在 snapshot 前转为 typed cancelled/recoverable 状态或使用已提交的前一稳定 checkpoint。

**最终决策**

> 待讨论。

**关闭条件**

- v3/v4 encode/decode、兼容范围、稳定持久化 stage、失败行为和 migration 测试矩阵均已固定。

### B06 —— Interview 回合的 rewind 与稳定恢复点

**当前事实**

- `SessionService.view()` 目前只把 Main 的用户消息暴露为 rewind point；Interviewer 内的回答不会出现在 `/rewind` 选择中。
- 当前 `rewind()` 以时间戳截断 history，然后把所有 Agent 重建为默认 `AgentSessionState`、切回 Main 并清空 handoff。
- 该算法既无法恢复 Interview workflow step／answers／scores，也会错误结束正在进行的 Interview handoff。

**必须讨论**

1. 首版是否支持面试内 rewind；若暂不支持，如何显式拒绝而不是静默损坏状态。
2. rewind point 是每个用户回答前、每个问题前，还是只有整场面试开始前。
3. 回退后是否保留 active Interviewer handoff，并重新显示旧问题。
4. 已完成评估、报告或其他副作用如何撤销／标记失效；是否允许跨已提交报告 rewind。
5. turn identity 是否继续依靠 timestamp，还是 workflow 使用稳定 answer/question id。

**推荐方向（待确认）**

- 至少不要沿用当前通用重建逻辑处理 Interview state。
- 推荐把每个 `AWAITING_ANSWER` 作为稳定 checkpoint，以 question/answer stable id 回退；回退后保留 Main→Interviewer handoff，并删除该点之后的回答／评分。
- 若首片暂缓完整 rewind，应在 active Interviewer workflow 时返回明确 typed error，并把“支持面试内 rewind”设为后续强制门禁，而不是假装兼容。

**最终决策**

> 待讨论。

**关闭条件**

- rewind 支持范围、选择项、回退后的 active agent/handoff/state、跨副作用边界行为和测试场景明确。

### B07 —— 暂停、Esc 取消、停止面试、`/exit_sub` 与 handoff closure

**来自 B01 的已确认约束**

- 用户必须能够通过可发现的指定命令提前结束面试并获得明确标注为 partial 的部分报告；该入口必须是 typed lifecycle 语义，不能把普通自然语言伪装成面试答案。命令名称、状态转换和 handoff closure 仍由本条决定。

**当前事实**

- 当前 Esc／Ctrl+C 取消一次 Runtime blocking call；`Cancelled` 不自动关闭 active handoff，下一条用户输入继续发送给原 SubAgent。
- `/exit_sub false` 直接用 `FailHandoff` 关闭；`/exit_sub true` 则向当前 SubAgent 注入一条普通中文 `UserMessage`，要求模型总结并调用 `switch_to_mainagent`。
- 对确定性 workflow 而言，这条普通 `UserMessage` 可能被误判为面试答案；它不是 typed lifecycle command。
- Workflow 还需区分：取消当前 node、暂停整场、用户主动提前结束并生成部分报告、放弃并返回 Main、真实 failure。

**必须讨论**

1. Esc 取消后 workflow 回到哪个稳定 stage；下一条自由文本是重试、答案还是新指令。
2. “暂停稍后继续”“提前结束并总结”“放弃且不总结”“退出 SubAgent”如何触发。
3. 是否新增 typed exit/stop command，替代 `/exit_sub true` 的自然语言注入。
4. 完成整场面试时由 executor 直接产生 `HandoffRequested`，还是仍经 `switch_to_mainagent` ToolOutcome。
5. failure／cancel／stop 哪些保留 handoff，哪些闭合，并向 Main 返回什么 typed summary。

**推荐方向（待确认）**

- 保留 Esc 为“取消当前 blocking node、维持 active handoff”；executor 回到上一个稳定 checkpoint。
- 增加最小 typed lifecycle command 表达“请求退出／是否总结”，让 ReAct 与 Workflow executor 都能处理，停止依赖隐藏的中文 `UserMessage`。
- 用户主动提前结束与系统 failure 分离；前者可生成部分报告并正常 return，后者按现有 failure closure 返回 Main。

**最终决策**

> 待讨论。

**关闭条件**

- pause/cancel/stop/abandon/fail/exit 的触发、状态转换、handoff 处理、summary 和恢复行为全部可区分。

### B08 —— 回答、评分、进度、最终报告的数据所有权

**来自 B01 的已确认约束**

- MVP 在结束时统一展示报告，不显示逐题即时评分；报告必须由稳定、带版本的模板填充。未来 Observer Agent 的隔离逐题评分属于后续功能，本轮只需保证数据 owner 与 schema 不封死该扩展点。

**当前事实**

- `SessionState` 适合保存运行进度，但当前 agent history 只有通用 message/tool records，没有 typed question/evaluation/report aggregate。
- 当前 Artifact domain 明确是 Resume artifact：`LATEX/PDF/README` 与 copy/build/merge operation；它不是可直接复用的通用报告 repository。
- Memory 只允许保存 fact/preference，不是面试记录数据库。
- 当前没有 Interview 专用 repository，也没有已确认的报告导出格式。

**必须讨论**

1. question、raw answer、evaluation、score、follow-up、workflow progress 各自属于 Session state 还是独立 aggregate。
2. 最终报告首版只作为 Session 中的用户可见消息，还是要持久化为 Artifact；若为 Artifact，是扩展现有 aggregate 还是新建 interview report 边界。
3. 逐题评分是否持久化；用户是否能查看、导出、重建。
4. report 生成失败后能否重试，如何避免重复产物。
5. 哪些数据允许进入 Memory，是否必须用户逐次明确确认。

**推荐方向（待确认）**

- workflow progress、question、answer 和 evaluation 先由 typed Interviewer state 持有并随 Session snapshot 保存。
- Memory 默认完全排除面试 transcript、评分和报告；需要沉淀个人事实时走现有明确 consent／build 边界。
- 首个纵向切片可先把最终报告作为 Session 中的 typed report + 用户可见 Markdown；若必须导出文件，再单独设计 versioned report artifact，不直接硬塞进 Resume `ArtifactKind`。

**最终决策**

> 待讨论。

**关闭条件**

- 每类数据的 owner、schema、写入时点、读取／导出方式、失败与幂等语义明确。

### B09 —— 隐私、日志、auto-memory、删除入口与 retention

**当前事实**

- CLI 对每个 terminal Runtime event 调用 `finalize_turn()`；若 `AUTO_MEMORY_ON_EXIT=true`，会从当前 active Agent history 异步提取 Memory。
- `SessionService.memory_source()` 当前不会按 Agent 类型排除 Interview transcript。
- `AgentRuntime` DEBUG 记录完整模型原始回复；解析失败的 WARNING 也记录完整 `raw_reply`。模型回复可能复述用户回答、评分或求职敏感信息。
- Session 当前会持久化，但没有已确认的 Interview retention、删除入口或逐场 consent。

**必须讨论**

1. Interview transcript 默认是否持久化；保存前是否提示用户并取得同意。
2. 明确 retention：无限、固定天数、用户关闭前、或由用户选择。
3. 删除粒度：整场面试、单份报告、整个 Session；入口是新 CLI command、应用 API 还是暂不持久化。
4. auto-memory 是否对 InterviewerAgent 强制关闭；手动 `/build-memory` 是否也拒绝或需要二次确认。
5. raw model reply 日志对 Interviewer 是否禁用、脱敏、截断或改为结构化 metadata；解析失败如何诊断。
6. snapshot、dump、artifact、普通日志分别允许包含哪些字段。

**推荐方向（待确认）**

- Interview transcript、评分和报告默认不进入 Memory；auto-memory 和手动 build 都必须有明确 Interviewer policy。
- 在没有删除入口和 retention 结论前，不授权长期持久化敏感评分／报告。
- Interviewer LLM 路径不记录完整 raw reply；保留长度、错误类型、workflow/node/turn id 等诊断 metadata。若用户要求原文诊断，必须显式 opt-in。
- 如果首版依赖 Session restore，则同时提供可发现的删除语义，并在启动面试前说明保存范围。

**最终决策**

> 待讨论。

**关闭条件**

- consent、持久化范围、Memory 策略、日志策略、删除入口和 retention 均明确，并有自动化拒绝回归。

### B10 —— question／rubric／JD 输入来源与版本化

**来自 B01 的已确认约束**

- MVP 不开放 `query_reference_data`、`query_memory` 或其他外部 tool call；问题由 Interviewer LLM 基于用户显式提供的 JD 与简历摘要生成，回答暂由同一 LLM 判断。B10 仍须固定 Prompt／rubric 版本、强类型输出和可复现 metadata。

**当前事实**

- 当前静态输入允许使用 `data/reference/` 和 `data/prompts/`；Knowledge 与 Memory 有独立生命周期。
- 尚无 Interview question bank、rubric schema、版本字段或 loader。
- 如果所有问题和评分标准都由单次 Prompt 临时生成，restore／回放／评估解释性会变弱；如果直接依赖 Knowledge 语义检索，结果也需要稳定 source/version 记录。

**必须讨论**

1. 首版问题来自固定 versioned reference、基于 JD 的 LLM 生成、Knowledge 检索，还是组合。
2. rubric 的最小 typed schema：dimension、weight、evidence、score range、pass/concern 等。
3. 每场面试是否记录 question/rubric version、source id、生成参数和目标语言。
4. JD、简历和用户背景如何进入 workflow；是否允许 Interviewer 查询 Memory／Knowledge，何时需用户确认。
5. 中文／英文面试是复用同一语义 rubric 还是维护语言版本。

**推荐方向（待确认）**

- rubric 使用项目内 versioned typed reference；问题可由 deterministic selector + LLM 结合目标岗位生成，但必须记录 source/version。
- JD 和用户明确提供的上下文进入 Session workflow state；首片不默认主动读取 Memory。
- response language 复用当前 resolved locale 注入；rubric 的评分维度与枚举保持语言无关，展示文本再本地化／由模型按目标语言生成。

**最终决策**

> 待讨论。

**关闭条件**

- question/rubric/JD 的 source、version、loader/port、语言策略和可复现 metadata 明确。

### B11 —— AgentSpec、capability、配置与 composition root 清单

**来自 B01 的已确认约束**

- MVP 的语言沿用当前 resolved response locale，题数默认 5，不支持自然语言修改；未来选择必须进入 typed state／command。首版不实现计时，只评审可替换计时模块的接口边界，且未来语音场景必须能区分生成、播放／听取、转写和作答等时间段。

**当前事实**

- `AgentKey` 没有 Interviewer key；production `AgentCatalog`、LLM map、Plan map、initial Session 和 Orchestrator 都显式写死 Main／Resume。
- `runtime_llms` fixture 要求键集合严格等于 Main／Resume，且每个 Runtime 拥有独立 LLM 与 CancellationToken。
- Settings 只有 Main／Resume／Memory model profile/temperature；只有通用 model call／timeout／repair 上限。
- Tool capability 需要按 Interview MVP 最小化，不能复制 Resume 的 workspace／artifact 能力。

**必须讨论**

1. 新 AgentSpec 的职责、prompt 片段、temperature/model profile 与 capability 白名单。
2. Interview workflow 是否需要独立 LLM 实例、CancellationToken、PlanService、ToolExecutor/ToolContext。
3. 新配置项及默认值：model profile、temperature、题数、追问数、整场调用预算、评分范围等；哪些复用全局配置。
4. Main 路由 descriptor 与 handoff contract 如何更新；首次接收 delegate 时是否继续“确认后等待下一条用户输入”。
5. production 新文件、公开类／方法、bootstrap wiring、ResourceStack ownership 和测试 fixture 的精确清单。

**推荐方向（待确认）**

- 使用 `AgentKey.INTERVIEWER`、独立 spec factory、独立 LLM 和 CancellationToken；不共享 Main/Resume runtime state。
- 初始 capability 只给真正需要的能力，候选为 `RETURN_TO_MAIN`；Memory、Knowledge、Workspace、Artifact、Web Search 均不默认开放。
- workflow budget 使用显式 Settings 并验证范围；provider timeout 和 format-repair policy 只有语义相同时才复用全局值。
- composition 继续显式装配和逆序释放，不引入 import-time registration。

**最终决策**

> 待讨论。

**关闭条件**

- AgentSpec、capability、Settings、依赖所有权、资源释放、文件／类／公开方法清单完整且可逐项审查。

### B12 —— 实施切片、回归矩阵、真实 smoke 与停止门禁

**当前事实**

- 当前只授权 Review，没有 coding 白名单。
- R9 会同时触及 domain、application、session schema、orchestration、CLI、bootstrap 与数据策略；一次性实现不可审查且难以回退。
- 现有工程要求纯 domain/application 逻辑有自动化保护，真实 provider／TTY 行为必须与 unit/static checks 分开记录。

**必须讨论**

1. 代码／测试／Prompt／reference／配置／文档的精确白名单。
2. 是否先做 protocol/state/schema 基础切片，再做纯 workflow domain，再做 executor/composition 纵向片。
3. 每片的定向测试、完整 unittest、compileall、diff-check、静态边界和 checkpoint。
4. property/transition tests、snapshot migration、rewind、cancel、handoff、privacy refusal 的覆盖矩阵。
5. 真实 provider／Windows TTY smoke：中文／英文、完整 main→interviewer→main、取消／恢复、报告、数据与日志边界。
6. 用户审查门禁与何时允许 checkpoint／进入下一片。

**推荐方向（待确认）**

```text
R9-P  文档 Review 与精确接口清单
R9-A  executor protocol + typed state + session schema migration
R9-B  纯 Interview workflow domain/transition
R9-C  Interviewer executor + command/event/lifecycle
R9-D  AgentSpec + prompt/reference + composition + Main routing
R9-E  persistence/rewind/privacy/report policy implementation
R9-F  完整工程验证 + 真实 provider/TTY smoke + 用户审查
```

- 每个切片独立验证、独立 checkpoint；白名单外问题停止并重新授权。
- B01～B11 未关闭前，不把上述候选切片视为最终计划。

**最终决策**

> 待讨论。

**关闭条件**

- 最终切片、逐片白名单、验收矩阵、提交边界、用户 review gate 和失败分流全部确认；用户随后另行明确授权 coding。

## 5. 当前审查结论

当前没有“技术上无法实现”的硬阻塞；B-01、B01、B02 已验证关闭。当前最高优先级回到 B00：继续固定全局 token ledger 的数据类型、写入时序、持久化分层与精确实现白名单。

下一条讨论从 **B00 —— 逐次 LLM token usage 的采集、归属、持久化与查询** 的 provider-neutral usage record 与 attempt 写入顺序开始；每次只更新已确认结论和依赖，不提前实施代码。
