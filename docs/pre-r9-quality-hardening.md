# R9 前质量加固计划

## 1. 文档状态与执行门禁

- **状态：** Q1～Q6 已完成代码、测试与独立 checkpoint；Q7 用户 smoke 1～5 已完成，第 6 项 Ubuntu/Linux lock/install smoke 有问题待后续处理，最终静态与文档 checkpoint 尚未完成。
- **目的：** 在进入 R9 前，按已确认边界修复当前 v2 的安全、结构、维护性与性能问题，并持续记录本轮明确暂缓的问题，避免后续遗忘。
- **执行入口：** 后续只有在用户明确要求开始本计划后，才从 Q1 按顺序执行。
- **停止边界：** 本计划独立于 R9；不得借质量加固检查、设计或实施 InterviewAgent、Workflow、Sticky Plan、Job Search 或其他 R9 功能。
- **状态真相：** `docs/current.md` 仍是项目唯一阶段快照；本文件只承载本轮 R9 前质量加固的执行清单和暂缓项。
- **数据边界：** 不得读取、迁移、改写或删除 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/`。现存 v2 session dump 也不得在未获单独数据操作授权时自动移动。
- **现有门禁：** HandoffContext、R8-F-C 与 query_memory 的真实 provider smoke 仍未完成；本计划的自动化结果不能替代这些 smoke。

## 2. 已确认设计

### 2.1 原始模型回复日志

- 保留解析失败时完整记录 `raw_reply` 的现有行为。
- 这是为 JSON 格式错误定位而接受的诊断策略，不作为本计划缺陷处理。
- 默认日志可能包含对话、简历、JD、客户文件内容或工具输出；部署或日志共享策略变化时再重新评估保留期限、访问权限和脱敏。

### 2.2 LaTeX 编译

- `build_pdf` 调用 `pdflatex` 时增加 `-no-shell-escape`。
- 保留参数 tuple、默认 `shell=False`、工作区路径约束、审批、超时与取消行为。
- 当前只保证不通过 TeX shell escape 执行系统命令；不在本轮引入容器、完整 TeX 沙箱或工作区外文件读取隔离。

### 2.3 客户文件读取

- 移除 `AuthorizedFileReader` 内部不可变路径授权集合。
- 授权由 `read_customer_file` 的逐次 `ConfirmationMode.ALWAYS` 审批承担。
- 保留绝对路径、支持格式、分页返回和每次调用独立审批；不得缓存或跨调用复用审批结果。
- 暂不新增或重命名公开 Reader 类型。

### 2.4 typed interaction

- 删除 `ToolInteraction.kind == "approval" / "selection"` 魔法字符串分支。
- 拆分为两个 typed outcome，例如 `ToolApproval` 与 `ToolSelection`；Runtime 使用 `isinstance()` 处理。
- 保留现有 `ApprovalRequested`、`SelectionRequested`、审批拒绝、选择取消和 handoff 状态语义。

### 2.5 Plan 投影

- 删除 Runtime 对 `create_plan`、`update_plan_status`、`cancel_all_plans`、`replan` 的工具名硬编码。
- 不让 Plan 工具通过 `ToolOutcome` 声明状态变化。
- 成功执行工具后比较执行前的 `AgentSessionState.plan` 与 `PlanService.snapshot()`；只有二者不同时，才把新 Plan 投影到 `ToolResultRecord`、Runtime state 和 `ToolFinished.plan`。
- 普通工具不得因存在活动 Plan 而重复触发 Plan UI。
- 保留 `SessionService` 现有的 Plan restore/snapshot 同步职责。

### 2.6 `_complete_model()`

- 本轮不拆分 `_complete_model()`，也不新增 Model coordinator/service。
- 解析、repair、取消、超时和状态转换的 early-return 流程继续集中维护。
- 将来只有在能提取纯构造逻辑且不会制造更多联合返回或隐式状态修改时，才考虑私有 helper。

### 2.7 Tool Schema 外层校验

- 保留未知参数允许列表投影、required 检查和现有外层类型检查。
- 新增 `allowed_values` 校验。
- 新增 list 的一层 `items` 类型校验；不递归解释 handler 的业务结构。
- 不注入默认值、不转换参数、不修改合法参数，也不删除 handler 现有防御性校验。
- 非法参数必须在 handler 运行前返回明确 `ToolFailure`。

### 2.8 Workspace write 与性能

- 不新增 `WorkspacePort.create()`。
- `workspace_write` 工具必须只在目标不存在时写入；目标已存在或在检查后被并发创建时均返回失败，不得覆盖。
- 为保留内部覆盖写入能力，可在现有 `WorkspacePort.write()` 上增加明确的 no-replace 选项；`workspace_write` 使用 no-replace，现有已确认覆盖路径继续使用默认 replace。
- `workspace_read` 只读取一次 `FileSnapshot`，直接从 snapshot 内容完成分页、总行数和 truncated 计算。
- `find_files` 恢复有限遍历：设置 `max_results` 时达到上限即停止，再排序已命中的有限结果。
- 保持对外默认值和返回结构不变：read 100 行、grep 50 条、文件搜索 50 条。

### 2.9 Session dump

- 新 dump 写入 `SESSIONS_DIR/dumps/<session_id>.json`。
- `JsonSessionRepository.list()` 只枚举 canonical session 文件，并忽略根目录历史 `*.dump.json`。
- 不自动移动、删除或改写当前根目录中的 11 个历史 v2 dump。
- 增加 dump 不出现在 restore 列表、canonical session 仍可恢复的测试。
- rewind 时间戳边界按当前单 worker、顺序执行约束接受，不在本轮修改。

### 2.10 CLI Rich markup

- 所有模型、工具、provider、文件和用户可控字符串在作为 Rich markup 输出前必须转义，或使用 `Text`／`markup=False`。
- 固定样式由 Renderer 自己构造；不能允许不可信内容注入 Rich tag。
- 覆盖 Progress、ToolStarted、ToolFinished 标题、审批、选择、handoff、错误、通知、Plan description、help description 和参数摘要。
- Markdown assistant 正文继续由 `Markdown` 渲染，不纳入 Rich tag 转义改造。

### 2.11 依赖升级

- 当前只升级已确认可解析的依赖：
  - `sentence-transformers 5.6.0 → 5.6.1`
  - `torch 2.10.0 → 2.13.0`
  - `setuptools 81.0.0 → 83.0.0`
- 不把 `torch` 或 `setuptools` 新增为直接业务依赖。
- 使用 uv 的定向升级和 universal lock；执行前确认没有并发 uv 操作。
- `chromadb 1.5.9` 当前无更高可用版本，不为消除审计提示而降级或切换来源；继续禁止暴露 Chroma Server，仅使用当前嵌入式 `PersistentClient`，并跟踪上游修复。
- 依赖升级后必须复核 Windows／Ubuntu/Linux lock 分支，以及 CUDA 12 → CUDA 13 的 Linux 传递依赖变化。

## 3. 执行切片

### Q1 —— TeX 与客户文件边界

- [x] `pdflatex` 增加 `-no-shell-escape`。
- [x] 增加命令参数测试，证明未启用 shell escape，且原有 cwd、timeout、cancellation 不变。
- [x] 移除 Reader 路径集合及对应拒绝逻辑。
- [x] 更新客户文件测试：未审批仍被 ToolExecutor 拦截；审批后可读取任意受支持的绝对路径；相对路径和不支持格式仍失败。
- [x] 运行 Resume/customer-file 定向测试、`compileall`、`git diff --check`。
- [x] 独立审查本切片 diff 后再进入 Q2。

### Q2 —— typed interaction 与 Plan 去硬编码

- [x] 定义 typed approval/selection outcomes，并迁移所有生产构造点和测试。
- [x] Runtime 改用类型分支，删除 interaction kind 字符串。
- [x] 删除 Plan 工具名集合。
- [x] 以 Plan snapshot 前后比较决定是否投影 Plan。
- [x] 增加非 Plan 工具在活动 Plan 下不重复渲染 Plan 的回归测试。
- [x] 增加 Plan 工具改名／自定义 Plan mutation handler 仍能投影 Plan 的测试，证明逻辑不依赖名称。
- [x] 不修改 `_complete_model()`。
- [x] 运行 Runtime、Plan、ToolCatalog 定向测试、`compileall`、`git diff --check`。

### Q3 —— Tool Schema 边界

- [x] 在 `ToolExecutor` 增加 `allowed_values` 检查。
- [x] 增加一层 list `items` 类型检查。
- [x] 锁定未知参数继续静默投影、默认值不注入、合法参数对象不被改写。
- [x] 增加 `copy_template(template="invalid")`、`provide_choices(choices=[1])`、`workspace_edit(edits=["invalid"])` 等边界测试。
- [x] 运行 ToolCatalog、Plan、Switch、Workspace、Resume 定向测试、`compileall`、`git diff --check`。

### Q4 —— Workspace no-replace 与性能

- [x] 在现有 `write()` 边界增加明确的 no-replace 写入模式，不新增 `create()`。
- [x] `workspace_write` 始终使用 no-replace；移除“先 exists 再 force replace”留下的竞态覆盖可能。
- [x] 保留 replace、edit、Artifact 等已有覆盖路径的语义。
- [x] `workspace_read` 改为单次读取 snapshot。
- [x] `find_files` 达到 `max_results` 后停止遍历。
- [x] 增加已存在目标、并发创建、单次读取和有限遍历的测试。
- [x] 运行 LocalWorkspace、Workspace tools、Resume Artifact 定向测试、`compileall`、`git diff --check`。

### Q5 —— Session dump 与 CLI 输出安全

- [x] 新 dump 写入 `sessions/dumps/`。
- [x] session list 忽略根目录历史 `*.dump.json`，不移动现存数据。
- [x] 增加真实 `JsonSessionRepository` dump/list/load 回归测试。
- [x] 对 Renderer 中不可信 Rich 字符串统一转义。
- [x] 增加含 `[bold]`、`[/]`、伪审批 tag 的 Progress、Tool、Approval、Selection、Plan、错误和通知测试。
- [x] 运行 Session、CLI commands、CLI app、bootstrap 定向测试、`compileall`、`git diff --check`；定向测试合计 60/60 通过，代码 checkpoint 为 `0beb960`。

### Q6 —— 依赖升级

- [x] 运行只读 outdated／audit，刷新执行时的真实版本和公告状态；升级前 6 个公告，升级后仅剩 `chromadb 1.5.9` 的 2 个无修复公告。
- [x] 定向升级 `sentence-transformers`、`torch`、`setuptools`；不新增无直接 import 的业务依赖，版本分别为 5.6.1、2.13.0、83.0.0。
- [x] 审查 `pyproject.toml` 与 `uv.lock`，确认 universal markers、CUDA 12→13 Linux 传递依赖和非目标包漂移；`pyproject.toml` 未新增直接依赖。
- [x] `uv sync --locked` 验证当前 Windows 环境。
- [x] 运行完整 unittest、`compileall`、`git diff --check`；293/293 unittest、`compileall` 与 diff-check 通过；测试迁移 checkpoint 为 `51ae04b`，依赖 checkpoint 为 `48e3773`。
- [x] 运行真实 Knowledge prepare/query/close smoke，确认 embedding、reranker 与 Chroma PersistentClient 正常；远端模型 HEAD 首次断开，使用已有本地模型缓存离线复核通过：ready、6 added、3 hits、worker closed。
- [ ] 在可用环境中完成 Ubuntu/Linux lock/install smoke；未执行时必须保留为开放门禁。
- [x] 重新运行依赖审计并记录 `chromadb` 的无修复例外与不可达边界；`chromadb 1.5.9` 仍有 2 个公告且无 fix version，不降级、不换源，继续保持嵌入式 PersistentClient 边界。

### Q7 —— 完整验收与文档 checkpoint

- [ ] 完整运行 `uv run python -m unittest discover -s tests/get_me_in -t .`。
- [ ] 完整运行 `uv run python -m compileall src/get_me_in main.py`。
- [ ] 运行 `git diff --check`、legacy import/path 静态扫描和 Catalog 数量复核。
- [x] 运行真实客户文件审批、Workspace no-replace、Session dump、CLI markup、Resume PDF build smoke；用户确认 Q7 真实业务 smoke 已完成。
- [x] 确认未读取、迁移、改写或删除四个 legacy 数据目录；用户确认 Q7 数据边界 smoke 已完成。
- [ ] 分离代码／测试、依赖和文档 checkpoint；不得把 R9 内容混入。
- [x] 单独完成 HandoffContext、R8-F-C 与 query_memory provider smoke；用户确认 smoke 1～4 已完成。
- [ ] 由用户完成最终审查后，才决定是否授权 R9。

## 4. 当前明确暂缓或接受的问题

下列项目必须保留在后续审查台账中，但不属于 Q1～Q7 当前实现范围。

### D1 —— Artifact committed replay 的文件验证

- **现状：** committed copy/build/merge replay 直接返回已记录结果，不验证输出仍存在或仍匹配原 hash。
- **暂缓原因：** 当前尚未维护 Artifact 版本／reconcile 生命周期，单独增加验证会引出缺失文件、内容漂移、重建和版本推进语义。
- **重启条件：** 开始 Artifact 版本维护、外部修改协调或 committed reconcile 设计时。

### D2 —— 完整 TeX 文件系统沙箱

- **现状：** 本计划只禁用 shell escape，不保证 TeX 不能读取工作区外的本地文件。
- **暂缓原因：** 当前是本机、显式审批的简历编译流程；完整限制需要 TeX distribution 配置、受限进程或容器。
- **重启条件：** 接受不可信第三方 `.tex`、服务化、多用户部署，或要求严格文件机密边界时。

### D3 —— Rewind 同时间戳碰撞

- **现状：** rewind 使用时间戳确定 turn 边界。
- **接受原因：** 当前单 session、单 worker 顺序执行，用户接受现有时间精度风险。
- **重启条件：** 多进程写 session、导入外部 snapshot、批量重放或观察到真实碰撞时。

### D4 —— `AgentRuntime` 整体拆分与 `_complete_model()` 重构

- **现状：** Runtime 较长，但仍围绕单 Agent typed transition 内聚；`_complete_model()` 包含连续的 provider／parse／repair／state 流程。
- **暂缓原因：** 机械拆分会增加隐式状态同步和联合返回；本计划只移除 interaction/Plan 局部硬编码。
- **重启条件：** 新增第二类 runtime executor、方法复杂度继续增长，或可以提取真正纯逻辑时。

### D5 —— ChromaDB 公告无可升级版本

- **现状：** `chromadb 1.5.9` 命中 Chroma Server 预认证代码注入公告，当前索引没有更高版本。
- **接受边界：** production 只使用嵌入式 `PersistentClient`，不得暴露受影响 Server/API 路径。
- **重启条件：** 上游发布修复、架构考虑远程 Chroma，或 dependency audit 信息变化时。

### D6 —— 原始模型回复日志

- **现状：** 格式解析失败时以 WARNING 保存完整 `raw_reply`。
- **接受原因：** 用户明确要求保留完整响应以定位 JSON 解析和 provider 输出问题。
- **重启条件：** 多用户／服务化部署、日志集中上传、日志访问边界变化或需要自动脱敏时。

### D7 —— 其余可读性与维护性审查

以下项目尚未达成具体改造方案，待 Q1～Q7 完成后单独审查，不得顺手混入：

- application/CLI 多处依赖标注为 `object`，现有 Port/Protocol 未贯穿所有边界。
- `bootstrap.py` 内嵌 Main AgentSpec、重复构造 Main／Resume Runtime，以及进程级环境变量副作用。
- `KnowledgeService.reload()` 的重复线性查找和逐 source 整体 manifest 写入。
- `JsonArtifactRepository.next_version()` 每次扫描完整历史。
- `BackgroundWorker._results` 终态结果不淘汰。
- Memory JSON 写入原子性、损坏记录隔离和仓库错误一致性。
- Ruff、静态类型检查、安全扫描、复杂度／覆盖率门禁是否纳入项目。
- 大量压缩为单行的 handler／service 代码是否统一格式化。

## 5. 变更白名单原则

- 每个 Q 切片实施前必须从本文件列出精确文件白名单。
- 发现需要修改白名单外的生产对象、Prompt、公开方法、依赖或数据时必须停止并提交最小扩展说明。
- 纯测试 fixture 漂移不得静默扩大生产设计。
- 代码／测试、依赖和文档变更保持可独立审查、可逆。
- 不删除测试、不放宽 typed contract、不用 mock 替代真实 adapter smoke。
- 不把本计划或其中任何 deferred item解释为 R9 授权。
