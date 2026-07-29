# 当前状态

**当前阶段：** R8 —— R8-D 执行清单已完成分析更新，等待用户审查与明确授权

**当前任务：** R8-D 遗留删除清单审查：确认删除白名单、安全快照、删除后验证、独立提交与回退步骤

**当前子任务：** 请用户审查 `docs/refactor-task.md` 的 R8-D 4.1～4.5 清单；当前只完成只读盘点与文档更新，未执行任何 legacy 删除。

**当前阻塞：** R8-D 执行仍未获得用户明确授权。当前盘点确认删除白名单为 51 个 Git 跟踪的 legacy 源文件，另有 3 个被忽略的 checkpoint 目录；11 个直接依赖均仍被 v2 使用，预计无需修改依赖。未经后续明确授权不得删除 legacy。

**会话交接说明：** R8-P 提交 `d91e37c`，R8-E 入口切换提交 `9fbeabc`。R8-O 与用户审查已完成，工程验证为 283 项自动化测试、`compileall`、`git diff --check`、import boundary、2 Agent／26 Tool／10 command Catalog、真实 Memory delete 和 legacy refusal smoke 全部通过；KnowledgeService 状态竞态已由 `9da3242` 修复。R8-D 清单现已细化为分析／授权、删除前安全快照、精确删除、删除后验证、独立提交与回退五组任务。只读盘点确认 8 个 legacy package 内 45 个文件加 6 个顶层 module，共 51 个 Git 跟踪删除目标；三个被忽略的 checkpoint 目录当前共 5 个文件；11 个直接依赖均被 v2 使用。当前仍未授权或执行删除，旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 及所有 legacy production modules 均不得改动。

**下一步：** 用户审查并确认 `docs/refactor-task.md` 的 R8-D 4.1～4.5 清单；只有收到明确执行授权后，才从 4.2 删除前安全快照开始，按清单完成独立 R8-D 提交。

174. **G6 原通过结论已由决策 175 撤销** — R6 六个切片完成后曾进入 R6-T，但审查发现交叉一致性、取消、关闭与测试退出问题；R7 始终未启动。
175. **撤销 G6 通过结论并授权 R6-F** — 用户确认 typed background job result、可取消 task callback、Memory delete finalize callback 与四个独立修复切片；全部复验前不得恢复 G6 结论或进入 R7/R8。
176. **R6-F 完成并重新通过 G6** — 四个修复切片独立提交，187 项自动化测试与 `compileall` 正常结束，真实 Chroma/embedder/reranker smoke 通过；再次停在 R6-T，等待用户审查。
177. **确认 R7 总体边界并提交具体清单审查** — R7-P、Resume capability/资源所有权、独立 Artifact repository、build-attempt 与 typed partial retry 已确认；当时的具体清单待确认状态已由决策 178 解除。
178. **确认 R7 具体清单与 temperature/log 补充** — 用户确认具体文件、对象、公开方法和七个切片；先以 R7-P0 恢复 Main `0.1`、Resume `0.2`、MemoryExtractor `0.0`，Artifact build log 采用有界、脱敏、UTF-8 安全截断。本会话只做文档 checkpoint，后续新会话可从切片 1 开始。
179. **R7-P0 temperature 契约完成并继续 R7** — `AgentSpec`、`LLMRequest`、AgentRuntime、MemoryExtractor 与 OpenAI adapter 已表达显式 temperature，非法 provider 请求在建连前拒绝；针对性测试通过。用户已授权自动继续后续已确认切片。
180. **R7-P 动态 session identity 完成** — 每次 Runtime transition 从唯一的 `SessionState` 注入 session id，并仅在该次工具执行中形成临时 ToolContext scope；restore／rewind 授权隔离与 handoff 传播已回归验证。
181. **Resume 双 Runtime composition 完成** — Resume 使用 immutable AgentSpec 和完整非路由 capability；Main/Resume 拥有不同的 Runtime、LLM、CancellationToken、PlanService 与 ToolContext，Session 和 Orchestrator 同时装配二者。
182. **Artifact 使用 operation aggregate 持久化** — `ArtifactOperation` 原子承载 Artifact 与 build-attempt 结果；`save_operation()` 保持唯一写接口，PENDING 可按同 key reconcile，COMMITTED 表示记录完整而非业务一定成功。
183. **R7-P5 ArtifactService 完成** — Resume 工具经 ArtifactService 使用 aggregate 的 PENDING→副作用→COMMITTED 提交；copy retry 与 PDF retry 均惰性 reconcile，构建异常也记录 attempt，metadata 失败仍返回 typed partial failure。
184. **R7-P6 production composition 完成** — Settings 提供 artifacts directory、PDF timeout 与日志上限；ArtifactService 成为 Main/Resume 共享但仅关闭一次的资源 owner。
185. **R7/G7 已完成并停在 R8 门禁前** — WorkspacePort 增加受限原始字节 `content_hash()`，真实中文／英文／双语模板均完成复制、README 读取与 pdflatex 编译；205 项自动化测试和 `compileall` 通过。
186. **撤回 G7 完成结论并记录 R7-T 审查问题** — R7 代码切片与既有测试事实保留，但审查发现 Artifact reconcile、typed partial failure、损坏记录 typed failure 与 G7 验收证据缺口；问题修复与完整复验前不得恢复 G7 或进入 R8。本 checkpoint 只记录状态，不实施。
187. **R7-T 修复完成并重新通过 G7** — 四类审查问题与编辑 smoke 新发现的 Windows CRLF 问题均已修复，五个独立提交通过针对性验证；最终 212 项自动化测试、`compileall`、`git diff --check`、四份真实 Resume PDF smoke 与已有简历 edit/replace smoke 通过。恢复 G7 完成结论并继续停在 R8 独立授权门禁前。
188. **R7-T2 审查再次撤回 G7 并细化 R8** — 212 项测试与静态验证仍通过，但最小复现确认 exception retry 会在第二次调用中误报成功、损坏的 committed build aggregate 会泄漏非 typed `IndexError`，且 composition root 构造失败清理不完整；修复并完整复验前不得进入 R8。R8 候选清单已拆为五个独立切片，尚待后续确认。
189. **R7-T2 修复完成并再次恢复 G7** — 三个独立提交闭合 aggregate validation、retry typed failure 与 construction cleanup；216 项测试、`compileall`、`git diff --check` 和真实中英文 PDF smoke 通过。继续停在 R8 独立授权门禁前。
190. **R8 设计审查收紧入口错误、回退配置与验收证据** — 五切片顺序不变；R8-E 增加启动异常退出码 `1` 契约，R8-P 保留 legacy rollback 配置，旧数据未读／未写使用不同证据，Catalog 固定为 2 Agent／25 tool／10 command。本轮只更新候选文档，R8 coding 仍未授权。
191. **授权 R8 实施并完成 R8-P** — 用户授权从 bootstrap 后开始 R8 并要求每个阶段 checkpoint；R8-P 以 `d91e37c` 完成，保持 R8-O 用户审查门禁不变。
192. **R8-E 已完成并建立入口回退点** — 根入口切换为 v2，入口契约测试与 222 项回归通过；`9fbeabc` 是 R8-D 前唯一需要 revert 的入口回退点。
193. **R8-O 前置审查修复入口诊断与关闭边界** — `8e43bd7` 使启动异常在所有允许日志阈值下仅向文件写完整诊断，并让 Worker／Application 关闭异常及 `CloseReport.issues` 对用户可见且返回 `1`；`45b5152` 对齐 README 与配置兼容别名说明。225 项回归与入口 smoke 通过，R8-O 仍未完成。
194. **恢复固定欢迎 banner 并暂缓主题客制化** — R8-O 将根入口切换后丢失的旧版欢迎体验认定为回归，允许新增 `Renderer.render_welcome()` 并在首次输入前调用一次；本次不修改 Settings，显示开关、标题、副标题和样式配置统一记录到 R9。完整 227 项测试与真实根入口 banner／`/exit` smoke 通过。
195. **Tool 提示词语义缺失阻断 R8-O** — 真实 system prompt 证明 v2 全部 25 个 Tool 只暴露精简描述、参数类型与必填项，旧版使用／禁用时机、预期输出、参数说明和默认值未迁移。用户明确要求必须修复；现存 legacy Tool 定义作为迁移基线，修复和真实 prompt／行为复验前不得通过 R8-O 或进入 R8-D。
196. **恢复 25 个 Tool 的完整 LLM-facing 语义** — 全部 legacy 定义均已找到并迁移到强类型 `ToolDefinition`／`ToolParameter`，真实 Main／Resume prompt 重新包含使用／禁用时机、预期输出和完整参数元数据；234 项测试与 production composition prompt smoke 通过，Tool 阻断解除，R8-O 仍未整体完成。
197. **恢复 legacy XML Tool prompt 结构与固定语义顺序** — Tool 外层恢复为 `<Tool name>`、`Purpose`、`UseWhen`、`DoNotUseWhen`、`Arguments`、`ExpectedOutput` 的固定顺序；Arguments 内由 v2 强类型 schema 生成有序 JSON，不恢复旧全局 Registry 或运行时边界。
198. **恢复 SubAgent XML prompt 并限定路由可见性** — Main 以 `<SubAgent name>`、`Name`、`Description`、`Responsibilities`、`HardConstraints` 的固定顺序看见可路由子 Agent；非 Route Agent 不注入列表。JobSearchAgent 仍是冻结的 legacy 测试壳，本次不扩展 production Catalog。
199. **恢复 Main／Resume 完整 CommunicationStyle** — v2 首次迁移缩写了 Tone／Verbosity／ExplanationStyle，并遗漏全部 StyleRules／StyleAvoids；现按 legacy 原始定义逐项恢复到 immutable AgentStyle，由 PromptRenderer 继续统一注入五个既有区块。
200. **恢复 Main／Resume 剩余 Agent prompt 元数据** — Role、Mission、Constraints 的动态字段按 legacy 原始语义与列表格式恢复；Resume 在 legacy 基线上追加两项 v2 强化硬约束，静态模板和所有运行时边界不变。
201. **收敛模型输出协议并由 Runtime 填充内部事件字段** — 模型只需输出最小业务字段并明确区分 InputFormat；当时将 OutputFormat 固定在 system prompt 最后的排序策略已由决策 213 取代。解析器移除双协议兼容并验证业务字段与条件组合。Runtime 生成事件／调用链 UUID、role、timestamp 与 plan_status，历史工具调用使用 `id=event_id`、`tool_call_id=call_id`，record 级 Plan 快照向后兼容持久化。
202. **多余模型字段采用允许列表投影而非格式修复** — 决策 201 中“内部／未知字段触发 repair”的部分被替代；Parser 忽略未消费的顶层字段，Runtime 始终重建可信内部字段。必需业务字段、类型与 finish/tool_call 条件仍严格验证。
203. **恢复 v2 provider JSON mode** — OpenAILLMAdapter 对所有 completion 显式发送 `response_format={"type":"json_object"}`，恢复 legacy provider 约束；AgentRuntime 与 MemoryExtractor 的输出均为 JSON 对象，Web Search 独立 adapter 不变，一次格式 repair 继续作为异常兜底。
204. **在单次模型修复前增加本地 JSON repair** — ModelReplyParser 在 `json.loads` 语法失败后调用 `json_repair.loads`，但修复结果仍必须是 JSON object 并通过严格业务校验；纯文本、JSON string／array、缺少 finish message 或其他语义错误不得本地归一化。本地修复失败或语义校验失败时沿用决策 172/203 的一次模型 repair，第二次仍失败才返回 typed failure。
205. **Main 的业务能力只由当前 SubAgent 穷尽定义** — Main 只保留 Plan、当前时间、选项交互、客户文件读取、记忆查询与切换 SubAgent 六类辅助／路由工具；工具不构成对外业务能力。`<SubAgents>` 是唯一且穷尽的当前业务能力来源，禁止根据产品名称、工具、历史、模型知识或未来规划推测能力。无匹配项时只说明暂不支持且不提供替代建议；问候可用用户语言介绍实际 SubAgent 能力但不暴露内部架构。
206. **空 Memory collection 返回空结果并以显式迁移准备真实测试** — v2 Chroma 已正常加载 reference 数据；尚无 v2 Memory 时，`query_memory` 的 collection-not-found 必须解释为零命中，其他 Chroma 异常继续上抛，并补充 adapter／Tool 回归。后续真实 Memory smoke 前先把当前两份 legacy Markdown 记忆显式转换为 v2 JSON 并建立索引；不得让 production v2 直接读取 legacy 路径，不修改或删除原文件。
207. **targeted Knowledge reload 只比较目标范围** — `/ragreload <target>` 的 observed sources 与 manifest diff 必须使用相同 target 范围，禁止把非目标 manifest entries 误判为删除；完整 reload 继续比较全部 source。真实 `/ragreload memories` 已证明只保留两条 memory unchanged 且不会删除 references。
208. **RAG 启动后台预热全部查询模型且不泄漏权重输出** — `KnowledgeIndexPort.prepare()` 在 startup reload 的既有后台串行边界内幂等加载 embedding 与 reranker；manifest 无变化仍必须执行，预热成功后才能进入可查询状态，失败可由显式 reload 重试。生产 CLI 在模型库首次导入前关闭 Hugging Face／tqdm／transformers 进度输出并限制相关 logger，首次用户查询不得承担模型构造或显示权重加载信息。
209. **选择交互取消不得提升为 Agent 或 handoff 取消（自动继续部分已由 224 取代）** — `SelectionRequested` 中 Ctrl+C／EOF 使用 `CancelSelection` 闭合当前 `provide_choices`，向当前 Agent 返回 typed cancelled tool result；不得复用全局 `Cancel`。选择取消后的自动模型继续已由决策 224 改为等待下一条用户消息。
210. **新增 Resume-only PDF 合并工具并纳入 Artifact aggregate** — `merge_pdfs` 按 first → second 合并两个工作区 PDF，可省略后缀且需审批；二进制 I/O 留在受限 LocalResumeArtifacts，ArtifactService 以源文件 hash 实现幂等并记录输出 hash/version/page count。Main 不可见，不增加通用二进制 Workspace API；当前 ToolCatalog 从历史 25 增至 26。
211. **uv 唯一默认镜像切换为 TUNA 并拆分依赖添加与同步** — `pyproject.toml` 只配置清华 TUNA，不设置平台限制、官方 PyPI、第二镜像或 PyTorch 专源；继续生成 Windows／Ubuntu/Linux universal lock。新增依赖统一先 `uv add <package> --no-sync`，再 `uv sync`；锁定前先排除并发 uv 操作并耐心等待。
212. **finish thinking 必须是非空用户可见摘要（已由决策 219 推翻）** — 历史上曾要求 `finish.thinking` 必须是非空、非纯空白字符串；该要求现已由决策 219 推翻。`tool_call.thinking` 继续可选。
219. **finish thinking 恢复为可选摘要** — finish 可以省略 `thinking`；`null`、空字符串或空白字符串均表示没有摘要，其他非空值必须是 string。`finish.message` 仍必须是非空 string；`tool_call.thinking` 规则不变。
213. **system prompt 顺序只由模板文件名决定** — PromptRenderer 仅按 `*.md` 文件名排序并拼接，不得在代码中强制移动任何模板；InputFormat／OutputFormat 分别重命名为 `07_input_format.md`／`08_output_format.md`，`09_reserved.md` 保持最后。格式修复仍从 canonical OutputFormat 文件读取。
214. **工具调用未知参数沿用 v1 静默忽略语义** — `ToolExecutor` 先将模型传入参数投影到工具 schema 的已声明字段，再执行必填／类型校验；未知字段（包括误混入 `event_payload` 的 `thinking`）不产生 `unexpected_argument`，也不传入 handler。R8-O 的真实 smoke 仍需继续完成。
215. **模型调用上限默认调整为 100 且 Main／Resume 计数独立** — `AGENT_MAX_MODEL_CALLS` 默认值由 12 调整为 100；该限制统计模型 completion（含 repair）而非工具 handler；Main 与 Resume 共享配置但在各自 `AgentSessionState` 中独立计数。R8-O 真实 smoke 仍待完成。
216. **模型回复解析失败暂停当前 SubAgent，由用户继续** — 最终 repair 仍失败时进入 `Paused/WAITING_FOR_USER`，不闭合 handoff、不回 Main；用户下一条消息继续发送给原 SubAgent。真正 provider／业务失败仍按 `Failed` 闭合 handoff。
222. **`/exit_sub` 默认要求 SubAgent 总结，false 允许直接退出** — `/exit_sub`、`/exit_sub true` 向当前 SubAgent 注入退出总结指令，由其调用 `switch_to_mainagent(summary)`；`/exit_sub false` 直接闭合原始 handoff，结果消息为“用户主动退出”。
223. **Esc 取消当前 SubAgent run 但保留 handoff** — SubAgent 返回 `Cancelled` 时不再自动执行 `FailHandoff`；保留 active SubAgent、handoff frame 和 Main 的等待状态，下一条用户消息继续进入原 SubAgent。`Failed` 仍按失败路径退回 Main。
224. **provide_choices 取消后暂停当前 Agent，下一条用户消息再继续** — `CancelSelection` 仍写入 `ToolResultRecord`，但当前 Agent 进入 `WAITING_FOR_USER` 并返回 `Paused("selection_cancelled", reason)`；CLI 不再自动发送 `Continue()`，下一条用户消息与取消结果一起发送给当前 Agent。该决定取代决策 209 中“取消后进入 `MODEL_QUEUED` 并继续模型循环”的部分。
225. **R8-O 完整通过并停在 R8-D 授权门禁前** — 用户确认完整人工 smoke matrix 无问题；工程侧 283 项自动化测试、静态检查、Catalog、真实 Memory delete 与 legacy refusal smoke 全部通过。KnowledgeService 状态读取与锁释放竞态由 `9da3242` 修复。R8-D 仍须用户后续明确授权，当前不删除任何 legacy 源码或旧运行数据。
226. **R8-D 执行清单细化并保持授权门禁** — 当前盘点确认 51 个 Git 跟踪 legacy 源文件、3 个本地 checkpoint 目录与 11 个仍被 v2 使用的直接依赖；执行拆分为删除前快照、精确 literal-path 删除、删除后验证、独立提交和逆序回退，禁止宽泛清理及任何旧运行数据访问。清单更新不构成删除授权。

**已暂缓：** InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan、CLI banner 客制化等增强统一放到 R9；R0～R8 只做 v2 重构

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
157. **`/rewind` 选择显示用户输入预览而非内部 turn_id** — CommandRegistry 使用“序号 + 清理后的用户输入预览”构建选择项，并保留 label→turn_id 映射；用户无需识别 UUID，RewindSession 仍接收精确 turn_id。
158. **`/restore` 选择显示会话预览而非内部 session_id** — SessionPreview 从最新主 Agent 用户输入派生短 preview；CommandRegistry 显示“序号 + 预览 + 保存时间”，并在内部映射到 session_id，CLI 不读取 snapshot/history。
159. **帮助从真实命令注册表排序并说明审批模式** — `help_entries()` 与 `completions()` 均按命令名排序；`/approval` 无参数切换，或接受 `prompt/auto` 显式设置。
160. **不保留 `/auto-approve-switch` 向前兼容** — 删除该 alias；审批偏好统一由 `/approval` 管理，避免一个“switch”命令反而要求参数的交互歧义。
161. **恢复 DeepSeek Web Search 的旧版请求契约并拒绝未执行调用** — v2 adapter 必须保留旧版两轮调用的精确 system/user 文本、`max_tokens=4096`、`web_search` function schema 和 `"Provide the result"` tool result；不能将 `<｜｜DSML｜｜tool_calls>` 这类未执行调用当作成功搜索结果。真实最小 provider smoke 已返回正常搜索摘要。
162. **R5 工具可见性使用强类型事件投影** — `ToolStarted` 携带 arguments 供 Renderer 脱敏摘要，`ToolFinished` 可携带只读 Plan 投影；Renderer 显示截断结果预览与 Plan 表格，不读取 Session，也不反解析工具输出字符串；Sticky Plan 仍暂缓。
163. **用户拒绝审批终止本轮而非触发模型重试** — `Reject` 必须记录拒绝的 tool result 闭合 pending call，随后返回 `Cancelled` 让 CliApp 立即回到输入；技术/业务执行失败仍作为 `ToolFinished` 交回模型自修复。
164. **审批交互使用明确选项而非 `y/N`** — InputController 的 `confirm()` 以 questionary 选项列表显示“✅ 执行 / ❌ 取消”，保持 v1 的可视化审批体验；返回值和 CliApp 的 Approve/Reject 协议不变。
165. **`/rewind` 在回退前捕获预填文本** — CommandRegistry 必须在调用 `RewindSession(turn_id)` 前从当前 `SessionView.rewind_points` 取得目标用户输入，并返回 `PREFILL`；回退后的投影可能已不含目标回合，不能用于反查。
166. **`/restore` 与 `/rewind` 的选择菜单提供取消项** — 两个交互菜单末尾固定显示“❌ 取消”；选择后仅返回 CLI，不调用 RestoreSession 或 RewindSession，也不依赖 Ctrl+C。
167. **G5 已通过且 R6 暂停** — 用户确认 V50–V56 smoke 可接受；临时 `scripts/v2_runtime_smoke.py` 已删除。R6 仍须先经新文件、类与公开方法清单确认，当前按用户指示不进入该阶段。
168. **R5 审查修复命令事件闭合与错误边界** — `/exit_sub` 通过 `CommandAction.DRIVE` 将 RuntimeEvent 交回 CliApp 继续推进；命令 handler 的预期异常统一渲染并返回输入循环。跨组件回归补齐后 134 项核心测试通过；R6 仍未开始。
169. **R6 重设一致性边界并增加强制终止门禁** — 保留 RetrievalPort，删除重复搜索 DTO 和旧 Facade/observer/daemon 形状；新增 RUN command path、immutable MemoryBuildSource、observed/indexed manifest、BackgroundWorker、ResourceStack 与 typed close report。R6/R7 不再并行；G6 后必须 checkpoint 并停在 R6-T，未经用户授权不得进入 R7/R8。当前只完成设计文档，R6 coding 未启动。
170. **R6 清单获确认并固定新会话实施入口** — 用户确认 `docs/refactor-design.md#69-knowledge-与-memory` 的 R6 文件、对象、构造依赖与公开方法清单；本会话只做文档 checkpoint，不写代码。新会话 bootstrap 后从 domain/ports/manifest diff 第一切片开始，每步独立验证提交；G6 后仍强制停在 R6-T，不得进入 R7。
171. **R6 前增加独立 `thinking` 契约修复门禁** — v2 必须保留静态 JSON 输出中的用户可见 thinking 摘要并按 `SHOW_THINKING` 展示和持久化，但 ConversationCodec 与 R6 MemoryBuildSource 必须剥离该字段；不得捕获 provider 原生 `reasoning_content`。R6 清单不变，但 coding 必须等待 G5-F 通过。
172. **R5-F follow-up 统一格式修复的唯一契约与重试边界** — finish 必须出现 string `thinking`；当时允许空字符串的部分已由决策 212 取代。tool_call 可省略或为空；格式失败注入具体解析错误与完整 canonical output format，只允许一次修复，第二次失败立即返回 `invalid_model_reply`。
173. **v2 显式装配日志并固定环境变量所有权** — v2 日志仅配置 `src.get_me_in` 命名空间并写入 `LOG_DIR/app.log`；DEBUG 才记录完整模型原始回复。v2 只消费 typed Settings 声明的变量，旧 `AGENT_MAX_ROUNDS` 不生效，实际调用上限由 `AGENT_MAX_MODEL_CALLS` 控制。
174. **G6 原通过结论已由决策 175 撤销** — R6 原六个切片完成并 checkpoint，但后续审查发现一致性、取消、关闭和测试退出缺口；该决定仅保留历史过程，不再代表当前门禁状态。
175. **撤销 G6 通过结论并授权 R6-F** — BackgroundWorker typed result/cancellation、Memory delete finalize、Knowledge 串行边界与四个修复切片已获确认；全部复验前不得进入 R7/R8。
176. **R6-F 完成并重新通过 G6** — 四个修复提交与 187 项测试、`compileall`、真实模型 smoke 共同闭合 G6；当前再次停在 R6-T，R7/R8 未授权。
177. **确认 R7 总体边界并提交具体清单审查** — R7 五项总体边界获确认；当时提交的具体清单和六个切片处于待确认状态，已由决策 178 的最终清单和七个切片取代。
178. **确认 R7 具体清单与 temperature/log 补充** — R7 具体清单和七个切片已确认；temperature 恢复显式 per-caller 契约，Artifact build log 固定上限、脱敏与诊断字段。当前会话只做文档 checkpoint；新会话从 R7-P0 开始。
217. **SessionSnapshot 持久化 agent turn_id 并兼容旧 handoff 快照** — `SessionSnapshotCodec` 写入并恢复 `AgentSessionState.turn_id`；对缺少该字段的旧 handoff 快照从 frame 的 source turn 补齐，字段存在但不一致时仍由严格校验拒绝。新增 round-trip 与 legacy handoff 回归，避免 `/restore` 将合法 handoff 误报为不一致。
