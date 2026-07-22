# 当前状态

**当前阶段：** R6-T —— R6 完成，等待用户审查（R7 未启动）

**当前任务：** R6-F 修复、G6 复验与 checkpoint 已完成

**当前子任务：** 无。停在 R6-T 强制终止门禁，等待用户审查。

**当前阻塞：** R7/R8 未获用户授权；不得自行推进。

**会话交接说明：** R6-F 已按四个独立切片完成：启动加载、reload cancellation 与 Knowledge 串行边界提交 `05c4956`；Chroma 可恢复 replace/delete 提交 `73a1c79`；typed background result、可取消 task callback 与 Memory build/delete 一致性提交 `79c0601`；延迟启动 worker、timeout-safe close、静态 memory prompt、真实 Chroma 兼容与 Settings 模型基线提交 `38708e2`。`uv run python -m unittest discover -s tests/get_me_in -t .` 正常退出并通过 187 项测试，`compileall` 通过，`uv run python -m scripts.r6_knowledge_smoke` 输出 `R6_SMOKE_OK hits=1 score=0.961208`。G6 已重新通过；未创建或修改 R7 文件，未切换旧 `main.py`，未执行 R8 清理。

**下一步：** 用户审查 R6-F 修复与 G6 证据；只有用户后续明确授权，才可提交 R7 设计清单。当前不得进入 R7 coding 或 R8。

174. **G6 原通过结论已由决策 175 撤销** — R6 六个切片完成后曾进入 R6-T，但审查发现交叉一致性、取消、关闭与测试退出问题；R7 始终未启动。
175. **撤销 G6 通过结论并授权 R6-F** — 用户确认 typed background job result、可取消 task callback、Memory delete finalize callback 与四个独立修复切片；全部复验前不得恢复 G6 结论或进入 R7/R8。
176. **R6-F 完成并重新通过 G6** — 四个修复切片独立提交，187 项自动化测试与 `compileall` 正常结束，真实 Chroma/embedder/reranker smoke 通过；再次停在 R6-T，等待用户审查。

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
172. **R5-F follow-up 统一格式修复的唯一契约与重试边界** — finish 必须出现 string `thinking` 但允许空字符串，tool_call 可省略或为空；格式失败注入具体解析错误与完整 canonical output format，只允许一次修复，第二次失败立即返回 `invalid_model_reply`。
173. **v2 显式装配日志并固定环境变量所有权** — v2 日志仅配置 `src.get_me_in` 命名空间并写入 `LOG_DIR/app.log`；DEBUG 才记录完整模型原始回复。v2 只消费 typed Settings 声明的变量，旧 `AGENT_MAX_ROUNDS` 不生效，实际调用上限由 `AGENT_MAX_MODEL_CALLS` 控制。
174. **G6 原通过结论已由决策 175 撤销** — R6 原六个切片完成并 checkpoint，但后续审查发现一致性、取消、关闭和测试退出缺口；该决定仅保留历史过程，不再代表当前门禁状态。
175. **撤销 G6 通过结论并授权 R6-F** — BackgroundWorker typed result/cancellation、Memory delete finalize、Knowledge 串行边界与四个修复切片已获确认；全部复验前不得进入 R7/R8。
176. **R6-F 完成并重新通过 G6** — 四个修复提交与 187 项测试、`compileall`、真实模型 smoke 共同闭合 G6；当前再次停在 R6-T，R7/R8 未授权。
