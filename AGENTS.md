# AGENTS.md

本文件为 Codex 在本仓库工作的稳定约定。阶段状态只以 `docs/current.md` 为准，不从本文件推断里程碑。

## 项目

**get-me-in** 是面向程序员的 CLI AI 求职助手，使用 Python 3.14 和多 Agent Hub-and-Spoke 架构。`refactor` 分支已将生产入口切换到 `src/get_me_in/` v2；R8-D 已删除 legacy production 源码，R8-G 文档归一化与 G8 已完成并通过最终用户审查，当前停在 R9 独立授权门禁前。

## 新会话恢复顺序

1. 必须先执行 `/project-bootstrap` 并读取 `docs/current.md`。
2. 始终加载 `current.md` 明确列出的四份核心活跃文档：
   - `docs/design.md`
   - `docs/plan.md`
   - `docs/task.md`
   - `docs/decision.md`
3. 若 `docs/current.md` 明确路由专项执行文档，只额外加载其当前指定的文件；不得从历史决策中的专项文件名推断当前路由。
4. `docs/current.md` 是唯一阶段快照；`design.md`、`plan.md`、`task.md` 已收敛为当前 v2 事实，不再存在并行的 `docs/refactor-*.md`。
5. 历史 baseline、audit、matrix 和 smoke 原文由 Git 保存；不要在 `docs/` 重新创建归档副本，也不得据此覆盖 `current.md` 的阶段与授权状态。

## R8 完成状态与 R9 授权门禁

R8-D 已由提交 `7514af3` 精确删除 51 个 legacy production 文件，并由 `c13d455` checkpoint。R8-G 5.1～5.6、完整 G8 与文档 checkpoint 已完成；决策 239 记录 G8 完成证据，决策 240 记录最终用户审查通过，决策 241 与提交 `860aaae` 记录完成态文档契约收口。R8 已完成，R9 未授权。

新会话必须：

1. 先执行 `/project-bootstrap`，读取 `docs/current.md`、决策 239／240／241 和 `docs/task.md` 的 R8 完成态。
2. 确认分支为 `refactor`、工作区干净、`HEAD` 包含 `7514af3`、`c13d455` 与完成态文档契约提交 `860aaae`。
3. 未取得 R9 单独授权前，只能审查 R8 完成状态，不得检查、设计或实施 R9。
4. 若后续发现 R8 回归，先记录最小问题与证据并取得对应授权；不得借修复之名进入 R9。

### R8-G 文件与行为边界（已完成）

R8-G 文档归一化仅修改了以下 8 个文档／示例配置文件：

- `.env.example`
- `README.md`
- `AGENTS.md`
- `docs/current.md`
- `docs/design.md`
- `docs/plan.md`
- `docs/task.md`
- `docs/decision.md`

R8-G 文档提交未修改 `main.py`、`src/`、`tests/`、`scripts/`、`data/`、`pyproject.toml` 或 `uv.lock`，未新增业务能力、runtime class、service、port、schema、公开方法或依赖。G8 暴露的 Settings 测试断言与 SubprocessRunner 缺陷均先停止 R8-G，经独立授权、修复和提交后才恢复验证；修复未混入 R8-G 文档／配置提交。

文档归一化已完成：

- 删除 `.env.example` 的 R8 观察期说明和 `legacy rollback only` 段，但保留 v2 正式变量及仍受支持的兼容别名。
- 把 README 从迁移／观察期说明改为已落地 v2 事实，记录当前入口、Main／Resume 能力、10 个 CLI 命令、配置和数据边界。
- 更新活跃文档与本文件的当前态；历史阶段和决策只保留为明确历史，`docs/decision.md` 只追加、不改写。
- Agent、Tool、命令和 Settings 数量／名称必须从实际 Catalog、Registry 与代码取证，不维护第二份运行时真相。

### G8 验证与提交（已完成）

已完成：

```powershell
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```

完成内容还包括：

- 扫描生产入口、v2 源码、测试和配置，确认无 legacy import、动态 import 字符串、旧模块路径或 import-time registration。
- 从 `AgentCatalog.list_descriptors()`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 复核 2 个 Agent、26 个 ToolDefinition、10 个 CLI 命令。
- 从真实根入口验证 Settings／启动退出码、基础对话、10 个 CLI 命令、handoff、审批／拒绝、Esc／选择取消、restore／rewind 和资源关闭。
- 验证真实 Chroma／embedder／reranker、Knowledge、Memory，以及中文／英文／双语 Resume copy／edit／build／open 和 `merge_pdfs`。
- 使用静态扫描、Settings sentinel 与拒绝访问 smoke 证明 production v2 不读取旧数据；mtime／hash 只能证明未改写。确认写入只落在 `data/workspace/` 与 `data/v2/`。
- 已审查 `git diff --name-status` 与 staged diff；R8-G 文档变更只涉及上述 8 个文件，独立代码／测试修复保持分离，G8 通过后已完成 R8-G checkpoint。

### 数据与回退边界

以下 legacy 用户运行数据永远不得读取、改写、迁移或删除：

- `data/save/`
- `data/memories/`
- `data/chroma/`
- `data/temp/`

当前 R8 完成态若需回退，先按逆提交顺序 revert `860aaae` 及其后的文档同步提交，再逆序 revert R8-G 文档 checkpoint，然后 revert `7514af3`，最后 revert `9fbeabc`。只有 legacy 源码恢复后才允许实际启用 legacy-only 配置；任何回退都不得读取、迁移、改写或删除旧运行数据。

## 常用命令

```powershell
uv run python main.py
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
uv lock
uv sync --locked
uv add <package> --no-sync
uv sync
uv remove <package>
uv run --with jupyter --with jupyterlab-lsp --with jedi-language-server jupyter lab
```

CLI 当前有 10 个命令：

- `/help`
- `/edit`
- `/dump`
- `/restore`
- `/rewind`
- `/ragreload`
- `/build-memory`
- `/exit_sub`
- `/approval`
- `/exit`

旧 `/auto-approve-switch` 仅是历史 baseline，不是当前命令。

## 当前 v2 架构

生产入口：

```text
main.py
  → src.get_me_in.cli.main.main()
  → Settings.from_env()
  → build_application()
  → CliApp
```

`src/get_me_in/` 采用显式分层：

| 层 | 主要职责 |
|---|---|
| `domain/` | immutable domain types、RuntimeCommand／RuntimeEvent、ToolOutcome、Session／Plan／Artifact／Knowledge 状态 |
| `application/` | AgentRuntime、Application、Orchestrator、SessionService、PlanService、KnowledgeService、MemoryService、ArtifactService |
| `ports/` | LLM、Workspace、Session、Knowledge、Memory、Artifact、Frontend、Clock、Subprocess 等边界 |
| `adapters/` | OpenAI、Chroma、JSON repository、本地 Workspace／Resume artifact、文件读取和进程执行 |
| `tools/` | 声明式 ToolDefinition 与薄 handler |
| `cli/` | 输入、命令、渲染和 WorkerRunner；只通过 Application/RuntimeEvent 交互 |
| `bootstrap.py` | 唯一 production composition root，显式装配并转移资源所有权 |

核心约束：

- Main 是唯一入口与路由中心；当前 production Agent 只有 Main 和 Resume。
- 子 Agent 之间不得直接通信，也不得持有或调度其他 Agent。
- `SessionState` 是唯一 canonical session owner；CLI 不访问 Agent 私有字段。
- Runtime 使用 typed command/event transition；审批、选择、handoff、取消、失败和暂停不得使用魔法 dict。
- Tool 通过显式 `ToolCatalog` 和 capability 可见性装配；禁止 import-time 注册或可变全局 runtime singleton。
- 每个 Runtime 拥有独立 LLM、CancellationToken、PlanService 和 AgentSessionState；Application/Orchestrator 负责 handoff。
- Workspace、Knowledge、Memory 和 Artifact 副作用只能经 application service 与 port 执行。
- Artifact operation 使用 PENDING → side effect → COMMITTED，并保留 typed partial failure 和幂等 replay。
- Knowledge reload 由 manifest 的 observed/indexed 状态和单 worker 串行化；真实 adapter 必须显式 close。
- 可恢复暂停与 failure 分离：模型回复最终解析失败、审批拒绝或选择取消返回 `Paused`，进入 `WAITING_FOR_USER`，保留活动 SubAgent/handoff，并等待下一条用户消息。
- run 取消与 failure 分离：Esc 返回 `Cancelled` 并进入 `CANCELLED`，活动 SubAgent/handoff 仍保留；下一条 `UserMessage` 继续发送给原 SubAgent。只有 `Failed` 才按失败路径闭合 handoff。

## 数据与配置

- 静态输入只复用 `data/reference/`、`data/prompts/`、`data/resume/template/`。
- v2 业务运行数据只写 `data/workspace/` 与 `data/v2/`；诊断日志默认写入 `data/logs/`，由 `LOG_DIR` 控制。
- `KNOWLEDGE_INDEX_MODE` 只接受 `persistent`／`memory`，默认 persistent。persistent 使用 `PersistentClient + JsonManifestRepository`；memory 使用 `EphemeralClient + InMemoryManifestRepository` 并在每个进程全量重建。两种模式均不得读取旧 `data/chroma/`，也不得暴露 Chroma Server／HTTP API。
- 环境由 `src/get_me_in/cli/main.py` 加载 `.env`，再由 `Settings.from_env()` 解析；v2 代码不得 import legacy `src.config`。
- `pyproject.toml` 只配置清华 TUNA 为默认 PyPI 镜像，不设置 `[tool.uv].environments`，保持 Windows 与 Ubuntu/Linux universal lock。
- 新增依赖先执行 `uv add <package> --no-sync`，再单独 `uv sync`；运行 `uv lock`／`uv add` 前先确认没有并发 uv 锁定操作。

## 工作约定

- 新增文档使用中文，可保留代码标识符、命令、路径、协议名和产品专有名词。
- 项目遵循 **Plan → Execute → Result Validation → Replan**；完成阶段后使用 `/project-checkpoint`。
- 使用同步代码，不引入 `asyncio` 或异步框架。
- 运行项目 Python 代码必须使用 `uv run`。
- `refactor` 分支已授权核心自动化测试；纯 domain/application 逻辑必须有自动化保护，真实 LLM、Chroma、LaTeX 与 CLI 交互使用集成或 smoke 验证。
- 不得通过删除测试、放宽 typed contract 或用 mock 掩盖真实 adapter 问题来获得绿灯。
- Agent key、capability、状态和事件使用声明式常量／枚举，不写裸字符串控制协议。
- v2 禁止 import legacy package；`tests/get_me_in/test_import_boundaries.py` 持续维护 forbidden module 防回归。
- 新模块、公开类或公开方法必须先确认设计和清单；R8-G 不允许创建或修改这些对象。
- R0～R8 继续冻结 InterviewAgent、LearningAgent、完整 Job Search、Sticky Plan 和其他 R9 功能。
- 保留用户已有工作树变更；删除或移动前必须解析并核对精确绝对路径。
- 禁止 Bash/Python 脚本直接读写项目文件；使用专用读取、搜索和补丁工具。
- `docs/current.md` 新增决策摘要时必须同步追加 `docs/decision.md`。

## 文档

| 文件 | 用途 | 加载时机 |
|---|---|---|
| `docs/current.md` | 唯一当前状态快照：阶段、任务、阻塞、下一步和活跃文档路由 | 每次新会话必读 |
| `docs/design.md` | 当前 v2 架构、迁移边界和未来设计备忘 | 涉及架构、边界或 R8 删除范围时 |
| `docs/plan.md` | 里程碑、依赖、验收和停止门禁 | 排期、进入阶段或检查验收时 |
| `docs/task.md` | R0～R8 主执行清单与状态标记 | 开始、完成或审查主任务时 |
| `docs/decision.md` | 按编号追加的历史决策与理由 | 需要追溯边界或新增重要决定时 |
不要重新创建 `docs/refactor-design.md`、`docs/refactor-plan.md` 或 `docs/refactor-task.md`。
