# 重构实施计划

> 适用分支：`refactor`
>
> 工作流继续遵循 **Plan → Execute → Result Validation → Replan**。本文只描述重构顺序与验收门禁；任务粒度见 `docs/refactor-task.md`，目标架构见 `docs/refactor-design.md`。

## 1. 总体策略

本次采用受控重写，不在旧 `BaseAgent`、`App` 和全局 Registry 上继续叠加功能。v2 在 `src/get_me_in/` 中独立构建，旧实现作为行为基线保留到切换入口完成。

执行原则：

- **纵向切片优先：** 每个里程碑都形成可运行链路，不按“先写完所有 domain，再写完所有 adapters”横向铺开。
- **显式依赖：** v2 只允许 bootstrap/composition root 创建具体 adapter；禁止 import-time 注册和可变全局单例。
- **协议先行：** RuntimeCommand、RuntimeEvent、ToolOutcome、SessionSnapshot 先稳定，具体 Agent 后迁移。
- **保持同步：** 不引入 asyncio；阻塞调用由受控 worker thread 执行并接受 CancellationToken。
- **功能冻结：** R0-R8 期间不在旧架构上增加 Interview/Learning 等新功能。
- **可回退：** 入口切换与旧代码删除分成不同提交，确保切换后仍能回退。
- **文档真实：** v2 只有实际通过验收后才标记完成，不提前改写旧 `docs/design.md`。

## 2. 里程碑

### R0 —— 基线冻结与决策门禁

**目标：** 明确重构范围、行为基线和验证方式，避免重写过程中不断改变目标。

**产出：**

- 当前能力、缺失能力、架构问题和重复代码清单。
- `refactor-design.md`、`refactor-plan.md`、`refactor-task.md`。
- 用户确认 R-D1～R-D6。
- 自动化测试已获授权；明确 unit/contract/integration/Notebook 的边界。
- 记录 `data/reference/`、`data/prompts/`、`data/resume/template/` 作为唯一保留资产；旧运行数据不迁移。

**验收门禁 G0：**

- 用户确认目标架构、迁移策略、功能冻结范围和验证策略。
- 明确哪些当前行为必须兼容，哪些可直接废弃。
- 未确认前不创建 v2 代码文件。

**依赖：** 无。

### R1 —— v2 骨架与 Composition Root

**目标：** 建立无全局可变状态的最小应用，可以构造两个互相隔离的 Application 实例。

**产出：**

- `src/get_me_in/` 包与 domain/application/ports/adapters/interfaces 分层。
- typed Settings 替代 import 时校验并 `sys.exit()` 的 SimpleNamespace；第三方环境变量设置集中在 bootstrap 最前端。
- Clock、IdGenerator、LLMPort、SessionRepository 等最小 ports。
- bootstrap 显式装配，不再通过导入 tool 模块触发注册。
- 最小 Main Agent spec 与 prompt renderer。

**验收门禁 G1：**

- v2 可完成一轮无工具 LLM 对话。
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
- 参数 schema、未知参数、缺失必填参数和 ToolCallException 的 v2 等价处理。
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
- versioned SessionSnapshot、codec 和 JSON repository；v2 使用全新会话，不提供 v1 migration。
- Session repository 默认写入全新 `data/v2/sessions/`，不读取旧 `data/save/`。
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
- `/help`、`/edit`、`/dump`、`/restore`、`/rewind`、`/exit_sub`、`/exit`、`/approval prompt|auto` 迁移；保留 `/auto-approve-switch` alias；`/ragreload`、`/build-memory` 先注册为明确 unavailable，真实 handler 在 R6 通过 registry replace 接入。
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

### R6 —— Knowledge/RAG 与 Memory 迁移

**目标：** 消除 RAG/Memory 全局 Facade 与回调式隐式索引，建立显式生命周期和可恢复一致性。

**产出：**

- 保留现有 tool-facing RetrievalPort；新增 KnowledgeSourceRepository、KnowledgeIndexPort、ManifestRepository、IndexManifest 与 KnowledgeService。
- Chroma adapter、embedder、reranker 与 loader 显式装配。
- 内容 hash 增量索引，正确处理新增、更新、删除和重命名。
- MemoryRepository、MemoryExtractor、MemoryService。
- build/query/delete 与 lifecycle close。
- `/ragreload`、`/build-memory` 的真实 CLI handler 通过 `CommandRegistry.replace()` 替换 R5 unavailable spec。
- Application 使用统一逆序资源清理栈关闭 loader/index 等资源。
- v2 Memory 使用全新 repository；不读取或迁移 v1 Memory 文件。

**验收门禁 G6：**

- reference 与 memory query 达到当前可接受结果。
- 文件删除后索引不残留；索引失败有可重试状态。
- 两个 Application 实例的服务生命周期可预测，不依赖模块全局状态。
- 退出时等待受控后台工作并有明确 timeout 结果。

**依赖：** G3；可在 R4-R5 后并行设计，但集成验收在 G5 后。

### R7 —— Resume 纵向切片与产物管理

**目标：** 用 ResumeAgent 验证 v2 的完整产品链路，而非只验证框架。

**产出：**

- 声明式 Resume AgentSpec 与 capability 集合。
- 保留 R3 已迁移的 copy template、README 读取、workspace edit/replace、build PDF、open preview 工具契约，以 ArtifactService 替换临时 ResumeArtifactPort adapter。
- ArtifactService/ArtifactRepository 记录 LaTeX 和 PDF 产物，不混入 Memory。
- JD 输入、简历修改、编译错误修复的完整流程。

**验收门禁 G7：**

- 新建中文、英文或双语简历流程可完成。
- 修改已有 LaTeX、编译 PDF、失败后重试、用户拒绝操作均可完成。
- ResumeAgent 不含重复的 14 个 `_get_*()` 方法。
- 当前 ResumeAgent 已实现能力达到等价后，才允许切换主入口。

**依赖：** G3、G4、G5；可与 R6 并行实现。只有实际使用 knowledge/memory 的 Resume 验收路径依赖 G6，G7 最终验收仍需相关路径完成。

### R8 —— 入口切换与旧代码删除

**目标：** 将生产入口切到 v2，完成一次可回退观察后删除遗留架构。

**产出：**

- `main.py` 指向 v2 bootstrap。
- 验证 `data/reference/`、`data/prompts/`、`data/resume/template/` 可被 v2 读取；不迁移旧 session/memory/temp/chroma 数据。
- 更新 `docs/design.md`、`docs/plan.md`、`docs/task.md` 和 AGENTS.md 为已落地架构。
- 删除旧 BaseAgent、App、Request/Response、UIBridge、全局 registries/facades 和兼容层。
- 确认临时 `scripts/v2_runtime_smoke.py` 已在 R5 删除，不保留第二入口。
- 清理 `.ipynb_checkpoints` 等不应进入源码树的文件。

**验收门禁 G8：**

- 完整 smoke matrix 全部通过。
- 仓库中不再存在 v2 对旧架构的 import。
- 旧入口删除前有独立可回退提交；删除后工作区与数据迁移说明完整。
- 文档工具数、Agent 数和实际 Catalog 一致。

**依赖：** G6、G7。

### R9 —— 新功能恢复

**目标：** 在稳定架构上重新启动产品功能开发。

**候选顺序：**

1. InterviewAgent。
2. Job Description 分析与 JobSearch 数据源决策。
3. LearningAgent。
4. Sticky Plan。
5. 多会话/其他前端。

这些功能需要分别重新确认接口、职责边界、依赖关系和方法清单，不属于本轮架构迁移的默认范围。

**依赖：** G8。

## 3. 关键依赖顺序

```text
R0 → R1 → R2 → R3 → R4 → R5 → R7 → R8 → R9
                         └────→ R6 ────┘
```

R6 的内部设计可在 R4/R5 期间进行；R6 与 R7 可在 G5 后并行，但 R8 必须等待 G6、G7 均完成。R8 之前旧实现保持可运行。

## 4. 风险与控制

| 风险 | 控制措施 |
|------|----------|
| 双实现长期并存 | 每个阶段设置切换门禁；R8 是明确清理里程碑 |
| 重写期间行为漂移 | R0 冻结 capability matrix；每阶段对照当前行为 |
| 重写回归 | 核心 domain/application 使用已授权的 unit/contract tests；adapter 走 integration/smoke |
| 误用旧运行数据 | bootstrap 只装配保留的三类静态资产；v2 数据目录与 schema 明确隔离 |
| LLM provider 无法可靠 abort | 隐藏在 adapter；允许 request-scoped transport，不污染 Runtime |
| RAG 模型慢导致开发反馈差 | ports 使用轻量 fake/manual fixture；真实模型在集成门禁验证 |
| CLI 跨平台退化 | Windows 为主验证，Unix 路径/键盘逻辑保留独立 adapter |
| 新架构过度设计 | 只实现当前纵向切片需要的 port；未使用扩展点不提前抽象 |

## 5. 计划更新规则

- 每次只允许一个重构阶段处于 🔄。
- 阶段开始前确认该阶段新文件、类和公开方法清单。
- 验收失败先记录原因并 replan，不得直接推进下一门禁。
- 不适用的任务直接删除或用 ⛔ 标明替代任务；历史由 Git 保存。
- 暂缓但仍有效的任务用 📌。
- 完成一阶段后由用户审查，再使用 `/project-checkpoint` 更新项目状态。
