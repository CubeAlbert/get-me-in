# 实施计划

> 适用分支：`main`
>
> 工作流继续遵循 **Plan → Execute → Result Validation → Replan**。本文只描述重构顺序与验收门禁；任务粒度见 `docs/task.md`，目标架构见 `docs/design.md`。

## 1. 总体策略

本次采用受控重写，不在旧 `BaseAgent`、`App` 和全局 Registry 上继续叠加功能。当前架构已在 `src/get_me_in/` 中独立构建，根入口已完成切换并通过 R8-O；R8-D 已由 `7514af3` 删除 legacy production 源码并完成 checkpoint，R8-G 文档归一化与完整 G8 已完成并通过最终用户审查。当前停在 R9 独立授权门禁前。

执行原则：

- **纵向切片优先：** 每个里程碑都形成可运行链路，不按“先写完所有 domain，再写完所有 adapters”横向铺开。
- **显式依赖：** 只允许 bootstrap/composition root 创建具体 adapter；禁止 import-time 注册和可变全局单例。
- **协议先行：** RuntimeCommand、RuntimeEvent、ToolOutcome、SessionSnapshot 先稳定，具体 Agent 后迁移。
- **保持同步：** 不引入 asyncio；阻塞调用由受控 worker thread 执行并接受 CancellationToken。
- **功能冻结：** R0-R8 期间不在旧架构上增加 Interview/Learning 等新功能。
- **可回退：** 入口切换与旧代码删除分成不同提交，确保切换后仍能回退。
- **文档真实：** 任务只有实际通过验收后才标记完成；重构前文档由 Git 保留，不在当前文档中并行维护。

## 2. 里程碑

### R0 —— 基线冻结与决策门禁

**目标：** 明确重构范围、行为基线和验证方式，避免重写过程中不断改变目标。

**产出：**

- 当前能力、缺失能力、架构问题和重复代码清单。
- `design.md`、`plan.md`、`task.md`。
- 用户确认 R-D1～R-D6。
- 自动化测试已获授权；明确 unit/contract/integration/Notebook 的边界。
- 记录 `data/reference/`、`data/prompts/`、`data/resume/template/` 作为唯一保留资产；旧运行数据不迁移。

**验收门禁 G0：**

- 用户确认目标架构、迁移策略、功能冻结范围和验证策略。
- 明确哪些当前行为必须兼容，哪些可直接废弃。
- 未确认前不创建新架构代码文件。

**依赖：** 无。

### R1 —— 架构骨架与 Composition Root

**目标：** 建立无全局可变状态的最小应用，可以构造两个互相隔离的 Application 实例。

**产出：**

- `src/get_me_in/` 包与 domain/application/ports/adapters/interfaces 分层。
- typed Settings 替代 import 时校验并 `sys.exit()` 的 SimpleNamespace；第三方环境变量设置集中在 bootstrap 最前端。
- Clock、IdGenerator、LLMPort、SessionRepository 等最小 ports。
- bootstrap 显式装配，不再通过导入 tool 模块触发注册。
- 最小 Main Agent spec 与 prompt renderer。

**验收门禁 G1：**

- 新架构可完成一轮无工具 LLM 对话。
- 同进程构造两个 Application，不共享 history、cancel 或 active agent。
- domain/application 不 import OpenAI、Chroma、questionary、Rich 或旧 `src.agents.base`。

**依赖：** G0。

### R2 —— Agent Runtime 与强类型事件协议

**目标：** 用显式状态机替换 BaseAgent 的 `_pending_*` 标志和 Request/Response 遗留协议。

**产出：**

- AgentSpec、RuntimeState、ConversationRecord union。
- RuntimeCommand/RuntimeEvent tagged union。
- ModelReplyParser 与 prompt/message codec。
- AgentRuntime 单步状态机：LLM reply、格式修复、未知工具、最大轮数和错误返回。
- CancellationToken 贯穿 Runtime 与 LLMPort。

**验收门禁 G2：**

- finish、invalid JSON 修复、unknown tool、timeout、cancel 均产生确定类型事件。
- Runtime 不 import CLI，不返回 magic dict，不暴露私有状态给调用方。
- 中断一次 LLM 调用后，下一次请求仍能正常执行。

**依赖：** G1。

### R3 —— Tool Runtime、Plan 与 Workspace

**目标：** 迁移最复杂的公共执行能力，消除 ToolRegistry、plan context 和 workspace 全局 read cache。

**产出：**

- 显式 ToolCatalog、Capability 与 ToolContext。
- ToolSuccess/Failure/Handoff/Interaction 等 ToolOutcome。
- 参数 schema、未知参数、缺失必填参数和 ToolCallException 的等价处理。
- 独立 PlanService 与 PlanState。
- LocalWorkspace 统一路径校验、编码、原子写、revision/read-before-edit。
- 现有通用、Plan、workspace、resume tools 的薄适配器。

**验收门禁 G3：**

- 工具成功、业务失败、框架异常、审批拒绝、取消均能闭合 tool call。
- 不存在 `_plan_agent`、`_current_bridge` 或进程级 `_read_files`。
- 两个 session 对同一 workspace 的 read revision 不互相授权。
- 25 个现有工具明确标注为“迁移、合并、替代或废弃”，目录可由 ToolCatalog 实时生成。

**依赖：** G2。

### R4 —— Session Aggregate 与 Hub-and-Spoke 编排

**目标：** 让会话和 Agent 切换成为 application 层能力，CLI 不再修改 Agent history。

**产出：**

- SessionState、AgentSessionState、HandoffFrame、SessionTurnView、SessionView；不提前定义 R7 Artifact schema，也不把 CLI input history 放入 domain Session。
- 现有 RuntimeState 并入 AgentSessionState，AgentRuntime 改为接收规范状态并返回 RuntimeTransition，不保留第二份长期状态。
- Orchestrator 执行 main→sub→main；切换时用 context 启动目标 Runtime，并通过 CompleteHandoff/FailHandoff 统一闭合正常返回、启动失败、嵌套、取消和失败路径的 handoff tool call。
- versioned SessionSnapshot、codec 和 JSON repository；当前架构使用全新会话，不提供 legacy migration。
- Session repository 默认写入全新 `data/runtime/sessions/`，不读取旧 `data/save/`。
- 原子 save、restore、rewind、dump。
- Plan、pending action、handoff stack 随 snapshot 一致恢复；conversation records 使用 turn_id 作为 rewind 边界。
- 每个 Application 同时管理一个活动 Session；ToolContext、CancellationToken、Plan 与 workspace revision grant 按 session/agent 装配。

**验收门禁 G4：**

- main→测试专用 sub Agent→main 的 context、turn id、call id 和 summary 完整闭环；真实 Resume Agent 留到 R7。
- restore 后 active agent、plan、pending action 与切换栈一致。
- rewind 不产生孤立 TOOL_CALL，也不遗留与截断历史不匹配的 Plan/pending state。
- snapshot 不重放活动 LLM/Process 或 TOOL_READY 副作用；restore/rewind 清除 workspace revision grant。
- CLI/application 只使用公开 Session API。
- SessionView 提供 `/rewind` 所需的只读用户回合投影；snapshot 拒绝与 active agent、pending call 或 turn 不一致的 handoff frame。

**依赖：** G3。

### R5 —— CLI 拆分与交互迁移

> **R5 前复审门禁（强制）：** G4 完成并 checkpoint 后、提交 R5 新文件/类/公开方法清单前，必须基于实际落地的 Application、SessionView、ApplicationCommand/RuntimeCommand、RuntimeEvent、handoff 与 cancellation 边界重新 Review R5～R8。重点复核：R5 CLI/WorkerRunner 是否仍为薄层；R6 命令接入与统一资源关闭是否仍匹配；R6/R7 并行和最终验收依赖是否合理；R8 删除清单、临时 Runner 删除时点与回退步骤是否完整。复审结论未记录前不得开始 R5 coding。

**目标：** 将旧 App 拆为薄 shell，使命令、输入、渲染和 worker 可独立替换。

**产出：**

- CliApp、CommandRegistry、InputController、Renderer、WorkerRunner，以及 `python -m src.get_me_in.cli` 独立入口。
- `/help`、`/edit`、`/dump`、`/restore`、`/rewind`、`/exit_sub`、`/exit`、`/approval`（无参数切换，或显式 `prompt|auto`）迁移；不保留 `/auto-approve-switch`；`/ragreload`、`/build-memory` 先注册为明确 unavailable，真实 handler 在 R6 通过 registry replace 接入。
- RuntimeEvent 驱动 confirm/select，不再使用 UIBridge。
- 单 WorkerRunner 串行调用 Application；Spinner 与 Esc/Ctrl+C cancel 只存在于 WorkerRunner/Renderer，跨线程只调用 `request_cancel()`。
- CLI input history 只使用进程内 CLI-owned state；restore/rewind 与 context recap 来自公开 `SessionView.rewind_points`，不增加独立持久化 schema。
- `Completed/Failed/Cancelled` 后自动 snapshot；保存失败不覆盖原 RuntimeEvent。
- G5 通过后删除临时 `scripts/v2_runtime_smoke.py`。

**验收门禁 G5：**

- 所有当前 CLI 命令有明确迁移状态和帮助文本。
- 命令新增不需要修改 CliApp 主循环分支。
- UI interaction 不阻塞或污染业务 Runtime 状态。
- HandoffRequested 后可直接 Continue 已启动的目标 Runtime；WorkerRunner 不并发访问 Application。
- 终态自动保存、restore/rewind、审批策略与 unavailable R6 commands 通过自动化测试。
- Windows UTF-8、Ctrl+C、Esc、编辑器失败路径行为明确。

**依赖：** G4。

**实施顺序：** CommandRegistry 强类型协议 → InputController/Renderer → WorkerRunner → CliApp event driver → 独立模块入口与 G5 smoke。每一步独立验证和提交；G5 前不接入 R6/R7 实现。

### R5-F —— LLM `thinking` 契约修复

**目标：** 修复新架构在解析 JSON `thinking` 后立即丢弃的契约偏移，恢复决策 135/136 的“保留但不回放”语义，并在 R6 复制会话用于 Memory 前固定敏感展示数据边界。

**产出：**

- `finish` 模型回复必须携带 string `thinking` 摘要；`tool_call` 可选携带。该字段是由静态输出 prompt 约束的用户可见推理总结，不是 provider 原生 `reasoning_content`。
- `MessageRecord` 和 `ToolCallRecord` 保存可选 thinking；AgentRuntime 将 parser 结果写入记录和对应 RuntimeEvent，`Completed` 与 `ToolStarted` 均可供前端读取。
- Session snapshot 对 assistant message/tool call 的 thinking 做可选字段 round-trip；缺失字段按 `None` 兼容当时的 snapshot，不迁移 legacy 数据，不重放活动副作用。
- Settings 增加独立 `show_thinking`，从 `SHOW_THINKING` 读取；Renderer 只在该值为 true 且摘要非空时展示“思考摘要”。`LLM_THINKING_ENABLED` 仍只控制 provider 端 thinking 模式。
- ConversationCodec 对所有发往 LLM 的历史记录显式排除 thinking；不得把前轮摘要写入 JSON message，也不得读取 provider 原生 `reasoning_content`。
- 仅修改既有 OutputFormat 模板（当前文件名为 `data/prompts/general_agent/09_output_format.md`）、`domain/messages.py`、`application/model_reply.py`、`application/runtime.py`、`application/events.py`、`application/conversation_codec.py`、`application/session_codec.py`、`application/settings.py`、`cli/renderer.py`、`cli/main.py` 与对应既有测试；不创建新代码文件，不修改 R6/R7 service。

**验收门禁 G5-F：**

- finish 缺少或错误类型 thinking 时走既有一次格式修复；tool_call 缺少 thinking 仍合法。
- finish/tool call thinking 可在当前事件和 snapshot round-trip 中保留；`SHOW_THINKING=false` 不显示但不破坏记录。
- 第二次及后续 LLMRequest 的所有历史消息均不包含 thinking；provider `reasoning_content` 仍不会进入 domain。
- CLI 在 `SHOW_THINKING=true` 时分别对最终回复和工具调用展示摘要；既有 Runtime、Session、CLI 与 25 个工具契约测试全部通过。
- 完成独立提交和 checkpoint 后才允许 R6 coding；R5-F 不创建或修改任何 R6 文件。

**依赖：** G5。R6 新增依赖 G5-F；R6 已确认的总体设计、文件清单与第一切片内容不变。

### R6 —— Knowledge/RAG 与 Memory 迁移

**目标：** 消除 RAG/Memory 全局 Facade 与回调式隐式索引，建立显式生命周期、可恢复一致性和受控的 CLI/ApplicationCommand 执行边界。

**产出：**

- 保留现有 tool-facing RetrievalPort/RetrievalResult；不再新增重复的 SearchQuery/SearchResult。
- 新增 KnowledgeSourceRepository、DocumentChunker、KnowledgeIndexPort、ManifestRepository、versioned IndexManifest 与 KnowledgeService；不迁移 v1 RagLoader/Facade 形状。
- Chroma adapter、embedder、reranker、source scanner、chunker 与 manifest repository 显式装配，禁止读取旧全局 config。
- 内容 hash 增量索引，正确处理新增、更新、删除和重命名；manifest 记录 observed/indexed hash、chunk ids、pending operation 与 error，失败可幂等重试。
- 新增 versioned JSON MemoryRepository、MemoryBuildSource、MemoryExtractor、MemoryService 与受控单 BackgroundWorker；JsonMemoryRepository 同时作为只读 KnowledgeSourceRepository 参与重启重建，不读取旧 Markdown Memory。
- Memory build/delete 显式执行 repository 与 KnowledgeService 协调；写入或删除部分成功必须返回 typed partial failure。
- 新增通用 `CommandAction.RUN` + ApplicationCommand/ApplicationResult worker path；`/ragreload` 前台可取消，`/build-memory` 后台非阻塞，并通过 `CommandRegistry.replace()` 替换 R5 unavailable spec。
- `Application.finalize_turn()` 统一终态 snapshot 和可选 auto-memory 排队，不向 CLI 暴露 Session history。
- Application 使用逆序、幂等、失败隔离的 ResourceStack；close 返回 error/timeout report。
- Memory 使用全新 repository；不读取或迁移 legacy Memory 文件。
- 删除 DeferredRetrievalAdapter 只能与真实 KnowledgeService 装配和 retrieval contract tests 同一切片完成。

**验收门禁 G6：**

- reference 与 memory query 达到当前可接受结果。
- 新增、修改、删除和重命名在 reload 后与 manifest/index 一致；失败保留 observed/indexed 差异和可重试状态，不误报全部成功。
- 两个 Application 实例的服务生命周期可预测，不依赖模块全局状态。
- `/ragreload` 通过单 WorkerRunner 串行执行并可取消；`/build-memory` 复制不可变会话输入后后台执行，CLI 不阻塞。
- terminal snapshot、手动 build-memory 与可选 auto-memory 均不读取 CLI/Session 私有状态。
- 退出时逆序关闭所有顶层 owner，等待受控后台工作并有明确 error/timeout 结果；一个 close 失败不阻断后续资源。
- DeferredRetrievalAdapter 已删除，25 个工具签名与 retrieval_unavailable/cancelled 失败契约保持一致。
- 核心 domain/application contract tests、adapter contract tests 与真实 Chroma/model smoke 均有验收证据。

**依赖：** G3、G5、G5-F；R6 设计清单已由用户确认（决策 170），但 coding 必须等待独立 thinking 契约修复通过并 checkpoint。R6 与 R7 不再并行实施。

**R6-T 强制终止门禁：** G6 通过后执行 `/project-checkpoint`，将状态保存为“R6 完成、R7 未启动、等待用户审查”，然后立即停止。未经后续明确授权，不得提交 R7 设计清单、创建或修改 R7 文件、切换入口或执行 R8 清理。

#### R6-F —— G6 审查修复

R6-T 审查撤销决策 174 中“G6 已通过”的结论。R6-F 已获用户确认，只修复既有 R6 契约，不进入 R7：

1. 接通后台启动加载、前台 reload cancellation 与 KnowledgeService search/mutation 串行边界。
2. 修复 Chroma replace/delete 的失败传播、旧索引保留与幂等重试。
3. 为 BackgroundWorker 增加 operation cancellation 和 typed job result；Memory build/delete 返回并保留 partial failure。
4. 修复 worker timeout 后的依赖关闭顺序、Application 测试 cleanup 与 composition root 构造失败清理。
5. 使用静态 memory prompt，补齐交叉 contract tests，重跑完整自动化测试、`compileall` 与真实 Chroma/embedder/reranker smoke。

**R6-F 验收：** 测试命令必须在打印结果后正常退出；启动后 reference/memory reload 可观察；Esc 可取消前台 reload；index/memory 任一步失败均不误报成功且可重试；worker timeout 不产生 use-after-close；真实 smoke 证据必须记录可复跑命令与结果。通过后重新认定 G6，并再次执行 R6-T checkpoint。R7 仍需后续明确授权。

**完成状态：** R6-F 四个切片已独立提交；187 项核心自动化测试与 `compileall` 正常结束，真实 Chroma/embedder/reranker smoke 可复跑且通过。G6 已重新认定通过并曾再次停在 R6-T；决策 177 已在后续会话确认 R7 总体边界，具体清单仍待最终确认。

### R7 —— Resume 纵向切片与产物管理

**目标：** 用 ResumeAgent 验证新架构的完整产品链路，而非只验证框架。

**产出：**

- 先完成 R7-P0：恢复 Main 0.1、Resume 0.2、MemoryExtractor 0.0 的显式 temperature 契约，不再依赖 provider 默认值。
- 先完成 R7-P：Runtime 每次从规范 SessionState 取得动态 session id，闭合连续 restore 后 workspace revision grant 与 artifact provenance 的 scope 漂移。
- 声明式 Resume AgentSpec 与已确认的 capability parity；Main/Resume 分别拥有 Runtime、CancellationToken、PlanService、ToolContext 与 LLM 生命周期。
- 保留 R3 已迁移的 copy template、README 读取、workspace edit/replace、build PDF、open preview 工具契约，以 ArtifactService 替换临时 tool-facing ResumeArtifactPort 实现，并继续借用低层 LocalResumeArtifacts backend。
- ArtifactService/ArtifactRepository 在全新 `data/runtime/artifacts/` 记录 LaTeX、README、PDF 与每次 build attempt，不混入 Memory，也不加入 SessionSnapshot 或随 rewind 回滚。
- Artifact operation 使用 pending → side effect → commit；文件成功但 metadata 失败时返回 typed partial failure，并可依据 deterministic operation key 重试 reconcile。
- build log 规范化 workspace 绝对路径，stdout/stderr 各按 `ARTIFACT_LOG_MAX_BYTES` 有界保存头尾内容，并记录原始 bytes 与 truncated flag。
- JD 输入、简历修改、编译错误修复的完整流程。

**验收门禁 G7：**

- 新建中文、英文或双语简历流程可完成。
- 修改已有 LaTeX、编译 PDF、失败后重试、用户拒绝操作均可完成。
- Main/Resume/Memory temperature 分别为 0.1/0.2/0.0，非法范围在 provider 调用前拒绝。
- 连续 restore 不跨 session 复用 workspace revision grant；Resume Artifact 记录使用当前 Session/Agent provenance。
- 非零退出、超时、取消、PDF 缺失与 metadata partial failure 均有 typed 结果且不误报可用 PDF；超长日志按确认策略截断且不破坏 UTF-8。
- Main/Resume capability、handoff、取消、Plan、save/restore/rewind 与 LLM/资源唯一所有权通过跨组件回归。
- ResumeAgent 不含重复的 14 个 `_get_*()` 方法。
- 当前 ResumeAgent 已实现能力达到等价后，才允许切换主入口。

**依赖：** G3、G4、G5、G6 以及 R6-T 后用户对进入 R7 的明确授权。不得与 R6 并行实现。

**实施顺序：** R7-P0 temperature contract → R7-P dynamic session identity → Resume AgentSpec/双 Runtime composition → Artifact domain/port/JSON repository → ArtifactService 与 copy/build/log 一致性 → Settings/bootstrap/resource ownership → 真实 Resume smoke 与 G7。七个原始切片、R7-T 与 R7-T2 均已独立验证和提交；决策 189 已再次恢复 G7。

### R8 —— 入口切换与旧代码删除

**目标：** 将生产入口切到新架构，完成一次可回退观察后删除遗留架构。

**产出：**

- R7-T2 已修复 Artifact exception retry、aggregate invariant 与 composition construction cleanup，并由决策 189 重新通过 G7；R8 不吸收这些缺口。
- R8-P 先校验静态资产、Settings／`.env.example`、capability、命令、Agent/tool 数量、当前架构→legacy import 和 legacy data 非访问边界；`.env.example` 与 README 保留清晰标记的 legacy rollback 段，不在切换前破坏旧入口回退条件。
- R8-E 将根 `main.py` 委托给当前 CLI，并补齐 composition／启动异常的用户可读错误和退出码 `1`；形成独立可回退 commit，不同时删除 legacy。
- R8-O 从根入口执行完整自动化与真实 smoke，验证入口退出码、CLI、Knowledge/Memory、Resume、handoff、审批／取消、restore/rewind 和资源关闭；用户审查通过前不进入删除。
- R8-D 已按精确清单由 `7514af3` 删除 51 个 legacy production 文件，并以 literal path 清理 3 个本地 `.ipynb_checkpoints`；`src/__init__.py`、完整 `src/get_me_in/` 和全部旧用户运行数据均保留。
- R8-G 已删除过渡期 legacy rollback 配置说明，README、AGENTS.md 及五份活跃文档已归一化为当前基线事实，完整 G8 与最终用户审查均已通过。设计／计划／任务文件名已由决策 227 提前收敛；辅助 baseline／audit／matrix／smoke 文档已由决策 228 收敛并删除，完整历史由 Git 保留。

**验收门禁 G8：**

- R8-E 前有通过的 G6／G7；R8-E 是可单独 `git revert` 的入口回退点，R8-O 通过并经用户审查后才允许 R8-D。
- 完整 unittest、`compileall`、`git diff --check` 与真实 smoke matrix 全部通过，`uv run python main.py` 是唯一生产入口。
- 仓库中不再存在当前架构对旧架构的 import，也不再存在清单中的 legacy production modules 或 `.ipynb_checkpoints`。
- `data/reference/`、`data/prompts/`、`data/resume/template/` 作为静态输入可用；旧 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 未被读取、改写、迁移或删除。“未读取”由静态扫描、sentinel Settings 路径断言和拒绝访问边界证明；mtime／hash 只证明未改写。
- `.env.example` 与 `Settings.from_env()` 一致；实际 Catalog 固定为 2 个 Agent、26 个 ToolDefinition、10 个 CLI 命令，文档名称和数量与 `AgentCatalog`、`ToolCatalog`、`CommandRegistry` 一致。
- 当前 R8-D 后、R8-G 前紧急回退按 `git revert 7514af3` → `git revert 9fbeabc`；未来 R8-G 提交后先 revert R8-G，再 revert `7514af3`，最后 revert `9fbeabc`，且始终不触碰旧运行数据。

**依赖：** G6、G7。

**实施顺序：** R7-T2/G7 → R8-P → R8-E → R8-O（强制停止／用户审查）→ R8-D → R8-G/G8。R8-P、R8-E、R8-O、R8-D、R8-G 与 G8 均已完成；G8 发现的代码／测试缺陷已按既定边界停止、独立授权、修复并提交。决策 240 完成最终审查，当前停在 R9 独立授权门禁前。

### R8-F-C —— 单一模型消息 Entity 与双格式投影修正（R8 后续，独立于 R9）

**目标：** 保留当前 `08_input_format.md` 和独立 `09_output_format.md`，让 history input 与 model output 成为同一个 `ModelMessageEntity` 的方向性投影；模型只提供输出方向所需字段，Runtime 补齐可信内部字段。既有三次 repair 与 snapshot 兼容继续保留。

**产出：**

- 新增 `ModelMessageEventType`、immutable `ModelMessageEntity` 与 `ModelMessageParseError`；Entity 的模型字段集合为 `id/role/timestamp/event_type/message/tool/tool_call_id/event_payload/thinking/plan_status`，并可携带不序列化的本地 repair 诊断。它是唯一 LLM-facing Entity，但各方向 required 字段不同。
- 新增 `ModelMessageCodec.encode(system_prompt, records)` 与 `parse(raw)`：history encode 将现有 ConversationRecord 投影为完整输入 Entity；reply decode 将 flat OutputFormat 投影为同一 Entity，再由 Runtime 生成 domain record。删除独立 `ModelReply` DTO。
- `08_input_format.md` 内容不修改；`09_output_format.md` 恢复 flat `event_type/message/thinking/tool/event_payload`，明确 tool_call 的工具名与参数，finish thinking 默认尽量提供但解析允许缺省。
- Runtime 生成／覆盖 id、role、timestamp、tool_call_id、plan_status；Plan 只从 Session canonical state 投影到下一轮输入 Entity，不接受模型回写。
- 保留 PromptRenderer 的文件名排序与 `render_output_format()`；full prompt 同时包含 InputFormat 和 OutputFormat，repair 只注入 OutputFormat。
- 保留 `format_repairs_used`、每 turn 3 次模型 repair、本地 JSON repair 不计数、第四次暂停、新 UserMessage 清零与旧 snapshot bool 兼容。

**范围：**

- 生产新增：`src/get_me_in/application/model_message.py`。
- 生产修改：`data/prompts/general_agent/09_output_format.md`、`src/get_me_in/application/runtime.py`、`src/get_me_in/bootstrap.py`。`PromptRenderer.render()`／`render_output_format()` 行为保持不变。
- 生产替换／删除：把 `src/get_me_in/application/conversation_codec.py` 与 `src/get_me_in/application/model_reply.py` 的有效逻辑迁入 `ModelMessageCodec` 后删除旧模块；不得删除或修改 `data/prompts/general_agent/08_input_format.md`。
- 测试新增／修改：`tests/get_me_in/test_model_message.py`、`tests/get_me_in/test_prompt_renderer.py`、`tests/get_me_in/test_runtime.py`、`tests/get_me_in/test_bootstrap.py`；迁移有效断言后删除 `test_conversation_codec.py`、`test_model_reply.py`。
- checkpoint：五份活跃文档。`domain/messages.py`、`ports/llm.py`、session codec/state、provider adapter、Settings、RuntimeEvent、工具、CLI、依赖和数据不在范围；确需改变时停止并提交最小扩展清单。

**验收门禁：**

- 实施前先锁定当前 `08_input_format.md` Git blob `50ee7a2a3c6cba3ea78d3f5efc5756f93d8199e4` 不变，并断言 `08_input_format.md`、`09_output_format.md`、`10_reserved.md` 均存在且顺序正确。
- Entity／codec 回归覆盖五类 input event、finish output、tool_call output、event_payload 参数、tool result correlation、plan_status 输入投影、Runtime-owned 字段重建和 thinking 输出保留／历史剥离。
- Prompt 回归必须证明 ToolCallFormat 明确展示 `tool` 与 `event_payload` 参数 object，finish 提示模型通常尽量提供 thinking，且 repair 仍只读取 `09_output_format.md`。
- 完整 unittest、`compileall`、`git diff --check` 与 diff 白名单审查通过后建立独立代码 checkpoint；实现会话负责回归，随后由用户执行真实 provider smoke。
- 本任务不构成 R9 授权；smoke 通过后才记录 R8-F-C 完成态。

**实施顺序：** 新会话 `/project-bootstrap` → 确认决策 249／干净工作区 → 锁定 InputFormat 与双文件顺序 → 新 Entity／codec contract → flat OutputFormat 与 reply decode → Runtime/bootstrap 接入 → 定向及完整自动化 → 独立代码 checkpoint → 用户真实 smoke → 文档 checkpoint。本会话只纠正文档，不修改代码或测试。

### R8 后续修正 —— tool call message 非空契约与 CLI 展示

**目标：** 修复 `tool_call.message` 允许空字符串且未进入 `ToolStarted`／CLI 的双重缺口；所有模型输出都由代码强制非空 message，finish 与 tool call 的 message 均保留 Markdown 展示能力，thinking 继续作为受 `SHOW_THINKING` 控制的纯文本摘要。

**产出：**

- 删除 OutputFormat 的 `<InputOutputDistinction>`，保留一个 `<Schema>`；message 使用 `minLength=1` 并允许 Markdown，finish thinking 在 Prompt 中要求为简短、用户可见纯文本，内部字段只说明无需提供。
- `ModelMessageCodec.parse()` 在事件分支前统一拒绝缺失、错误类型、空或纯空白 message；finish thinking 不新增 presence/non-empty 校验，既有三次 repair／第四次暂停边界不变。
- `ToolStarted` 增加必填 message；Runtime 使用关键字参数传递 message、thinking、tool 与 arguments，既有 `ToolCallRecord`／snapshot 无 schema 变化。
- Renderer 对 tool call 按 thinking Panel（开关开启时）→ Markdown message → 脱敏工具状态的顺序展示；Completed 的既有 thinking → Markdown message 顺序不变。

**范围：**

- Prompt／生产：`data/prompts/general_agent/09_output_format.md`、`src/get_me_in/application/model_message.py`、`src/get_me_in/application/events.py`、`src/get_me_in/application/runtime.py`、`src/get_me_in/cli/renderer.py`。
- 测试：`tests/get_me_in/test_model_message.py`、`tests/get_me_in/test_prompt_renderer.py`、`tests/get_me_in/test_runtime.py`、`tests/get_me_in/test_cli_commands.py`、`tests/get_me_in/test_bootstrap.py`。
- checkpoint：五份活跃文档；`08_input_format.md`、domain messages、session codec/state、provider、ToolDefinition／ToolExecutor、审批、handoff、Plan、Memory、数据与 R9 不在范围。

**验收门禁：**

- Prompt 回归证明无 `<InputOutputDistinction>`、仍只有一个 `<Schema>`、所有事件 message 非空、finish thinking 为纯文本提示约束且不暴露 Runtime 重建细节。
- Codec／Runtime 回归证明空白 tool-call message 进入 repair 且不执行工具，合法 ToolStarted 同时携带 message 与 thinking。
- CLI 回归证明 finish/tool-call message 均使用 Markdown；thinking 只按纯文本、受开关控制且显示在 message 上方；工具参数继续脱敏。
- 定向测试、完整 unittest、`compileall`、`git diff --check` 与白名单审查通过；Prompt/codec 与 RuntimeEvent/CLI 分别建立代码 checkpoint，完成态文档独立 checkpoint。

**实施顺序：** 设计文档 checkpoint → OutputFormat/codec 与定向测试 → 独立提交 → ToolStarted/Runtime/Renderer 与定向测试 → 独立提交 → 完整验证 → 完成态文档 checkpoint。任何必须扩展白名单的情况先停止确认；不得进入 R9。

**当前状态：** 已完成。设计 checkpoint `b190a06`、Prompt/codec checkpoint `0694c2b`、RuntimeEvent/CLI checkpoint `5a43fda` 已提交；定向 65/65 与 84/84、完整 unittest 296/296、`compileall`、diff-check、InputFormat blob 和 production-component smoke 通过。用户已完成 `SHOW_THINKING=false`／`true` 两组真实 provider／TTY smoke，确认 message 始终显示、thinking 仅在存在且开启时以纯文本 Panel 位于 message 上方；最终完成态文档独立 checkpoint。本修正关闭，仍不得进入 R9。

### 当前基线维护修正 —— Knowledge 取消作用域（已完成）

**目标：** 修复普通 Runtime Esc／Ctrl+C 在 Knowledge startup 仍为 `LOADING` 时误取消后台预热，并把 prepare cancellation 误记为 `ERROR`／`FAILED` 的问题；保持 `/ragreload` 可取消、后台 worker 有界关闭与真实 failure 可观测。

**实施顺序：** K0 只读诊断与计划（已完成）→ K1 Application 命令作用域 cancellation target → K2 Knowledge cancellation state／logging → K3 定向与完整回归 → K4 真实 cold-start／reload／exit smoke → 用户审查 → 完成态文档收口。

**范围：** 代码和测试白名单、目标契约、验证命令与停止条件已由决策 280～283、`docs/design.md`、`docs/task.md` 与 `docs/current.md` 承接。默认不修改公开 API、WorkerRunner、Chroma adapter、Settings、bootstrap、持久化、依赖或数据路径；需要扩展时必须停止确认。

**验收：** 普通 Runtime 取消只到 Session，startup Knowledge 继续到 `READY`；显式 `/ragreload` 取消保留已有可查询状态并可重试；worker-owned 取消为 `CANCELLED`，真实故障才为 `FAILED`；定向／完整 unittest、compileall、diff-check 与三个真实行为 smoke 全部通过。

**停止门禁：** 本修复独立于 R9。代码／测试与完成态文档分别提交；用户审查完成前不删除专项计划，也不得借修复进入 R9。

**完成结论：** K1～K4 已完成工程验证与 production composition smoke；用户确认普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 `/exit` 三项真实终端测试无问题。K5 已完成，五份核心文档同步收口，临时专项计划删除；本修复不构成 R9 授权。

### 当前基线多语言支持 —— UI locale 与模型回复语言（已完成，R9 仍未授权）

**目标：** 首版支持 `zh-CN`／`en-US`。CLI 自有文本由 strict locale catalog loader 和命名占位符生成；Main／Resume system prompt 注入统一 ResponseLanguage。UI、对话回复和 Resume artifact language 保持三个独立语义，不复制完整 system prompt，不改变模型消息 schema。

**范围：** 新增进程级 `UI_LOCALE`、`MODEL_RESPONSE_LANGUAGE`、`LOCALES_DIR`；新增 typed Locale、CLI Translator、两份 locale catalog 和 `07_response_language.md`；本地化 CLI-owned 文案，并将固定 Progress／审批展示语义改为 typed code／canonical tool name 后由前端翻译。当前类型与边界由 `docs/design.md`、`docs/task.md` 和代码保存；已完成切片的文件白名单由 Git 与决策 284～293 追溯。

**实施顺序：** L0 文档计划（本会话完成）→ L1 Locale／loader／Settings → L2 CLI-owned UI → L3 typed 固定事件文案与审批 → L4 ResponseLanguage Prompt → L5 完整验证与真实 provider／TTY smoke → L6 用户审查与文档收口。L1～L4 各自形成独立代码／测试 checkpoint；L5 原则上不修改 production；L6 文档独立 checkpoint。

**验收：** 两种 locale 的 catalog key／placeholder 严格一致；welcome、help、命令、输入、Session、Plan、Tool、审批、取消、错误和 application result 完成本地化且 Rich／Markdown／脱敏契约不退化；Main／Resume Prompt 都只含一个正确 ResponseLanguage；InputFormat／OutputFormat、ModelMessageCodec、snapshot、Memory build 和 Chroma 不变；完整 unittest、compileall、diff-check、静态 contract、双语言 component smoke 和双语言真实 provider／TTY 矩阵通过。

**已验证前提：** 当前 production Chroma、现有 embedding 和 reranker 已用英文技术栈与英文年龄查询正确 Top-1 召回中文 Memory；本专项不更换检索模型或重建索引。最终仍须验证真实模型在英文回合会按被动 Memory 契约调用一次 `query_memory` 并用英文回答。

**停止门禁：** L1～L6 已完成；不得增加 `/language`、自动检测、Session locale 字段、Prompt 多语言副本、Memory build 改造、依赖、索引迁移或 R9 工作。任何白名单扩展或 schema／公开 API 变化先停止确认；R9 仍需独立授权。

**当前状态：** L0～L4 代码／测试 checkpoint、L5 工程验证与用户确认的双语言真实 provider／Windows TTY 体验均已完成；L5 最终完整 unittest 为 `346/346`，代码／测试审查修复 checkpoint 为 `02c9c5d`。L6 README、五份核心文档和决策记录已完成，完成态专项执行文档已在最终事实合并后删除。本专项不构成 R9 授权。

### R9 —— 新功能恢复

**目标：** 在稳定架构上重新启动产品功能开发。

**候选顺序：**

1. R9-P：基于 R8 后实际边界 Review InterviewAgent Workflow；先确认职责、状态、交互、持久化、隐私和方法清单，不直接编码。
2. 若 Review 证明必要，以最小 typed executor protocol 解耦 Orchestrator 与具体 ReAct `AgentRuntime`，同时保持 RuntimeCommand/RuntimeEvent 和 handoff closure 稳定。
3. 建立 versioned Interview workflow state 与 snapshot/restore/rewind 语义，明确等待用户回答、暂停、取消和结束面试的区别。
4. 以“确定性 Workflow 外壳 + 节点内 LLM”实现 InterviewAgent 纵向切片，完成 main → interview → main、问题生成、回答评估、追问和总结。
5. 明确原始回答、逐题评分与最终报告的 Session/Artifact/Memory 所有权、隐私、删除和 retention。
6. Job Description 分析与 JobSearch 数据源决策。
7. LearningAgent。
8. Sticky Plan。
9. 多会话/其他前端。

**InterviewAgent 前置风险：**

- 当前 Orchestrator 与 `RuntimeTransition`／`AgentSessionState` 偏向单一 ReAct runtime，Workflow 不是零修改即插即用。
- `Completed` 当前同时表示 CLI 内层循环终止并触发 finalize；面试“等待下一次自由文本回答”的事件语义必须先确认。
- Workflow state 必须进入 Session 的 typed/versioned 唯一状态源，禁止藏在 runtime 实例、Plan、开放 metadata dict 或全局对象。
- workflow node 不是子 Agent；子 Agent 之间仍禁止直接 handoff。
- 原始回答、评分与报告涉及敏感数据，不得在未确定持久化和 retention 前默认写入 Memory 或日志。
- 当前“不引入 LangChain/CrewAI/AutoGen 等 Agent 框架”的决策保持有效；如需外部 workflow engine，必须单独重开架构决策。

**推荐门禁：** executor contract → workflow domain/state → snapshot/interaction → Interview vertical slice → privacy/report persistence → 真实 LLM smoke。每个门禁独立确认、验证和提交。

这些功能需要分别重新确认接口、职责边界、依赖关系和方法清单，不属于本轮架构迁移的默认范围。上述内容是避免遗忘的前置备忘，不代表 R9 coding 已授权。

**依赖：** G8。

## 3. 关键依赖顺序

```text
R0 → R1 → R2 → R3 → R4 → R5 → R5-F（thinking 契约修复） → R6 → R6-T（强制停止／用户审查） → R7 → R8 → R9
```

R6 与 R7 不再并行。R6 coding 与 G6 完成后必须先停在 R6-T；只有用户明确授权后才能进入 R7。R8 仍须等待 G6、G7 均完成，且在 R8 之前旧实现保持可运行。

## 4. 风险与控制

| 风险 | 控制措施 |
|------|----------|
| 双实现长期并存 | 每个阶段设置切换门禁；R8 是明确清理里程碑 |
| 重写期间行为漂移 | R0 capability 基线已收敛到 `docs/design.md` 第 2 节；每阶段从实际 Catalog 和验收证据复核 |
| 重写回归 | 核心 domain/application 使用已授权的 unit/contract tests；adapter 走 integration/smoke |
| 误用旧运行数据 | bootstrap 只装配保留的三类静态资产；当前数据目录与 schema 明确隔离 |
| LLM provider 无法可靠 abort | 隐藏在 adapter；允许 request-scoped transport，不污染 Runtime |
| RAG 模型慢导致开发反馈差 | ports 使用轻量 fake/manual fixture；真实模型在集成门禁验证 |
| CLI 跨平台退化 | Windows 为主验证，Unix 路径/键盘逻辑保留独立 adapter |
| 新架构过度设计 | 只实现当前纵向切片需要的 port；未使用扩展点不提前抽象 |

## 5. 计划更新规则

- 每次只允许一个重构阶段处于 🔄。
- 阶段开始前确认该阶段新文件、类和公开方法清单。
- 验收失败先记录原因并 replan，不得直接推进下一门禁。
- 到达阶段终止门禁时必须 checkpoint 并停止，不得以“下一阶段已有计划”为由自动推进。
- 不适用的任务直接删除或用 ⛔ 标明替代任务；历史由 Git 保存。
- 暂缓但仍有效的任务用 📌。
- 完成一阶段后由用户审查，再使用 `/project-checkpoint` 更新项目状态。
