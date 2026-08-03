# AGENTS.md

本文件为 Codex 在本仓库工作的稳定约定。阶段状态只以 `docs/current.md` 为准，不从本文件推断里程碑。

## 项目

**get-me-in** 是面向程序员的 CLI AI 求职助手，使用 Python 3.14 和多 Agent Hub-and-Spoke 架构。生产入口使用 `src/get_me_in/`，由 Main 统一路由各专业 Agent。

## 新会话恢复顺序

1. 必须先执行 `/project-bootstrap` 并读取 `docs/current.md`。
2. 始终加载 `current.md` 明确列出的四份核心活跃文档：
   - `docs/design.md`
   - `docs/plan.md`
   - `docs/task.md`
   - `docs/decision.md`
3. 若 `docs/current.md` 明确路由专项执行文档，只额外加载其当前指定的文件；不得从历史决策中的专项文件名推断当前路由。
4. `docs/current.md` 是唯一阶段快照；`design.md`、`plan.md`、`task.md` 只维护当前基线事实，不并行维护历史版本。
5. 已完成阶段的执行材料由 Git 和 `docs/decision.md` 保存；不要在 `docs/` 重新创建归档副本，也不得据此覆盖 `current.md` 的阶段与授权状态。

## 数据保护边界

以下 legacy 用户运行数据永远不得读取、改写、迁移或删除：

- `data/save/`
- `data/memories/`
- `data/chroma/`
- `data/temp/`

历史迁移、回退或新功能开发都不得绕过这项保护；具体历史提交与回退记录只从 Git 和 `docs/decision.md` 追溯。

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

CLI 命令、补全和帮助以 `CommandRegistry.help_entries()` 与 `CommandRegistry.completions()` 的实际结果为准，不在本文件维护第二份清单。

## 当前架构

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

- Main 是唯一入口与路由中心；可用专业 Agent 必须通过 `AgentCatalog` 显式装配并由 Main 路由。
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
- 业务运行数据只写 `data/workspace/` 与 `data/runtime/`；诊断日志默认写入 `data/logs/`，由 `LOG_DIR` 控制。
- `KNOWLEDGE_INDEX_MODE` 只接受 `persistent`／`memory`，默认 persistent。persistent 使用 `PersistentClient + JsonManifestRepository`；memory 使用 `EphemeralClient + InMemoryManifestRepository` 并在每个进程全量重建。两种模式均不得读取旧 `data/chroma/`，也不得暴露 Chroma Server／HTTP API。
- 环境由 `src/get_me_in/cli/main.py` 加载 `.env`，再由 `Settings.from_env()` 解析；当前代码不得 import legacy `src.config`。
- `pyproject.toml` 只配置清华 TUNA 为默认 PyPI 镜像，不设置 `[tool.uv].environments`，保持 Windows 与 Ubuntu/Linux universal lock。
- 新增依赖先执行 `uv add <package> --no-sync`，再单独 `uv sync`；运行 `uv lock`／`uv add` 前先确认没有并发 uv 锁定操作。

## 工作约定

- 新增文档使用中文，可保留代码标识符、命令、路径、协议名和产品专有名词。
- 项目遵循 **Plan → Execute → Result Validation → Replan**；完成阶段后使用 `/project-checkpoint`。
- 使用同步代码，不引入 `asyncio` 或异步框架。
- 运行项目 Python 代码必须使用 `uv run`。
- 核心自动化测试已获授权；纯 domain/application 逻辑必须有自动化保护，真实 LLM、Chroma、LaTeX 与 CLI 交互使用集成或 smoke 验证。
- 不得通过删除测试、放宽 typed contract 或用 mock 掩盖真实 adapter 问题来获得绿灯。
- Agent key、capability、状态和事件使用声明式常量／枚举，不写裸字符串控制协议。
- 当前代码禁止 import legacy package；`tests/get_me_in/test_import_boundaries.py` 持续维护 forbidden module 防回归。
- 新模块、公开类或公开方法必须先确认设计和清单。
- 保留用户已有工作树变更；删除或移动前必须解析并核对精确绝对路径。
- 在受限 Codex 沙箱中执行会写入 Git 索引或仓库元数据的 `git add`／`git commit` 时，直接申请对应命令的窄范围授权，不先执行一次已知会因 `.git/index.lock: Permission denied` 失败的普通尝试。该错误且无实际 lock 文件、无活动 Git／Git LFS 进程时按沙箱写权限不足处理，不得删除 lock 或修改 ACL；只有错误为 `File exists` 时才排查并发进程或 stale lock。
- 禁止 Bash/Python 脚本直接读写项目文件；使用专用读取、搜索和补丁工具。
- `docs/current.md` 新增决策摘要时必须同步追加 `docs/decision.md`。

## 文档

| 文件 | 用途 | 加载时机 |
|---|---|---|
| `docs/current.md` | 唯一当前状态快照：阶段、任务、阻塞、下一步和活跃文档路由 | 每次新会话必读 |
| `docs/design.md` | 当前架构、边界和未来设计备忘 | 涉及架构或边界时 |
| `docs/plan.md` | 里程碑、依赖、验收和停止门禁 | 排期、进入阶段或检查验收时 |
| `docs/task.md` | 主执行清单与状态标记 | 开始、完成或审查主任务时 |
| `docs/decision.md` | 按编号追加的历史决策与理由 | 需要追溯边界或新增重要决定时 |
