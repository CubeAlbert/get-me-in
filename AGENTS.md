# AGENTS.md

本文件为 Codex 在本仓库工作的稳定约定。阶段状态只以 `docs/current.md` 为准，不从本文件推断里程碑。

## 项目

**get-me-in** 是面向程序员的 CLI AI 求职助手，使用 Python 3.14 和多 Agent Hub-and-Spoke 架构。`refactor` 分支已将生产入口切换到 `src/get_me_in/` v2；legacy 源码暂时只为 R8-D 删除和紧急回退保留。

## 新会话恢复顺序

1. 必须先执行 `/project-bootstrap` 并读取 `docs/current.md`。
2. 只加载 `current.md` 明确列出的四份活跃文档：
   - `docs/design.md`
   - `docs/plan.md`
   - `docs/task.md`
   - `docs/decision.md`
3. `docs/current.md` 是唯一阶段快照；`design.md`、`plan.md`、`task.md` 已收敛为当前 v2 事实，不再存在并行的 `docs/refactor-*.md`。
4. 历史 baseline、audit、matrix 和 smoke 原文由 Git 保存；不要在 `docs/` 重新创建归档副本，也不得据此覆盖 `current.md` 的阶段与授权状态。

## 当前 R8-D 授权

用户已通过决策 227 明确授权在新会话执行 R8-D。本次授权边界如下：

- 从 `docs/task.md` 的 **R8-D 4.2 删除前安全快照**开始，依次完成 4.2～4.5。
- R8-D 只做 legacy 删除、删除敏感验证和独立提交；不新增业务能力，不新增 runtime class、service、port、schema 或公开方法。
- R8-D 提交并 checkpoint 后必须停止。不得自动进入 R8-G 或 R9。
- 如果发现需要扩大删除范围、修改公开协议、删除测试或猜测性移除依赖，立即停止并请求用户确认。

### Git 跟踪删除白名单

仅允许删除以下 8 个 legacy package 中已复核的 45 个 Git 跟踪文件：

- `src/agents/`
- `src/cli/`
- `src/llm/`
- `src/memory/`
- `src/prompts/`
- `src/rag/`
- `src/tools/`
- `src/utils/`

仅允许删除以下 6 个顶层 legacy module：

- `src/config.py`
- `src/lifecycle.py`
- `src/logger.py`
- `src/message.py`
- `src/request.py`
- `src/response.py`

当前 tracked 删除白名单总计 51 个文件。执行前必须用 `git ls-files` 重新生成并核对；若数量、路径或目录内容发生变化，停止并重新审查。

### 本地 checkpoint 清理白名单

以下 3 个目录被 Git 忽略，必须在确认 resolved absolute path 位于当前仓库内、且不存在意外内容或 reparse link 后，使用 literal path 单独删除：

- `.ipynb_checkpoints/`
- `src/.ipynb_checkpoints/`
- `src/llm/.ipynb_checkpoints/`

禁止使用 `git clean`、通配符、工作区根目录递归删除或从搜索结果拼接删除命令。checkpoint 删除只记录为本地证据，不伪装成 Git 提交内容。

### 必须保留

- `src/__init__.py`
- 完整 `src/get_me_in/`
- 完整 `tests/get_me_in/`
- `scripts/r6_knowledge_smoke.py`
- `data/reference/`
- `data/prompts/`
- `data/resume/template/`
- `data/workspace/`
- `data/v2/`

以下 legacy 用户运行数据永远不得读取、改写、迁移或删除：

- `data/save/`
- `data/memories/`
- `data/chroma/`
- `data/temp/`

证明“未读取”必须组合使用静态扫描、Settings sentinel 和拒绝访问 smoke；mtime／hash 只能证明未改写。

### 依赖边界

`pyproject.toml` 当前 11 个直接依赖均仍被 v2 使用，包括延迟导入的 `pdfplumber`、`python-docx`、`chromadb` 和 `sentence-transformers`。R8-D 预计保持 `pyproject.toml` 与 `uv.lock` 不变。

删除后必须复核使用证据；如果发现新的依赖清理候选，停止 R8-D 并单独提交审查，不得在删除提交中顺手移除。

### R8-D 验证与提交

删除后至少完成：

```powershell
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```

还必须：

- 扫描 `main.py`、`src/get_me_in/`、`tests/get_me_in/` 和生产配置，确认无 legacy import、动态 import 字符串或 import-time registration 依赖。
- 从实际 `AgentCatalog`、`ToolCatalog.export_descriptors()`、`CommandRegistry.help_entries()`／`completions()` 复核 2 个 Agent、26 个 ToolDefinition、10 个 CLI 命令。
- 完成根入口启动／`/exit`、production composition 和拒绝访问 4 个 legacy data 目录的删除敏感 smoke。
- 比较旧运行数据删除前后只读指纹／mtime，并确认保留路径完整。
- 审查 `git diff --name-status` 与 staged diff：R8-D 提交只包含已确认的 51 个 legacy 源文件删除。
- 创建独立 R8-D commit；不得混入 R8-G 文档、README、`.env.example` 或 v2 代码变更。

R8-D 前的入口回退点是 `9fbeabc`。R8-D 后紧急回退必须先 revert R8-D 提交恢复 legacy 源码，再 revert `9fbeabc` 恢复旧入口；恢复源码后才允许重新启用 legacy-only 配置。任何回退都不得触碰旧运行数据。

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
- cancelled interaction 与 failure 分离：Esc 或选择取消保留活动 SubAgent/handoff，并在 `WAITING_FOR_USER` 等待下一条用户消息。

## 数据与配置

- 静态输入只复用 `data/reference/`、`data/prompts/`、`data/resume/template/`。
- v2 运行数据只写 `data/workspace/` 与 `data/v2/`。
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
- 新模块、公开类或公开方法必须先确认设计和清单；R8-D 不允许创建这些对象。
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
| `docs/task.md` | 唯一执行清单与状态标记 | 开始、完成或审查任务时 |
| `docs/decision.md` | 按编号追加的历史决策与理由 | 需要追溯边界或新增重要决定时 |

不要重新创建 `docs/refactor-design.md`、`docs/refactor-plan.md` 或 `docs/refactor-task.md`。
