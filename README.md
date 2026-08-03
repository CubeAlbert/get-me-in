# get-me-in

面向程序员的 CLI AI 求职助手。生产运行使用 `src/get_me_in/` 下的当前架构，由 Main 统一路由专业 Agent 完成求职工作流。

## 运行入口

唯一生产入口是仓库根目录的 `main.py`：

```powershell
uv run python main.py
```

诊断时也可以调用同一套 CLI 模块入口：

```powershell
uv run python -m src.get_me_in.cli
```

启动前将 `.env.example` 复制为 `.env`，填写 OpenAI-compatible 服务地址、密钥和模型名称。配置由 `Settings.from_env()` 解析；静态输入目录由项目固定提供，运行目录由配置提供。

## 当前能力

`Main` 是统一入口和路由中心，根据 `AgentCatalog` 提供的专业 Agent 清单识别需求、收集必要上下文并切换 Agent。当前已落地的 Resume 工作流支持简历模板复制、读取、编辑、替换、PDF 构建、打开和 PDF 合并。

专业 Agent 与工具由代码显式装配，工具可见性按 Agent capability 隔离。实际清单以 `AgentCatalog.list_descriptors()` 与 `ToolCatalog.export_descriptors()` 为准。

## CLI 命令

CLI 命令由 `CommandRegistry` 注册并提供补全与帮助：

- `/help`：显示可用命令
- `/edit`：使用编辑器输入长文本
- `/dump`：导出当前会话
- `/restore`：恢复会话
- `/rewind`：回退到用户回合
- `/ragreload`：重载知识库
- `/build-memory`：构建当前会话记忆
- `/exit_sub`：退出当前子 Agent
- `/approval`：切换审批模式
- `/exit`：退出 CLI

命令名称、帮助文本和补全以 `CommandRegistry.help_entries()` 与 `CommandRegistry.completions()` 的实际结果为准。

## 数据与配置边界

生产运行复用的静态输入只有：

- `data/reference/`
- `data/prompts/`
- `data/resume/template/`

业务运行数据只写入：

- `data/workspace/`：工作区文件和会话可见的用户工作内容
- `data/runtime/`：session、Knowledge、Memory、Artifact 等持久化数据

Knowledge index 默认使用 `KNOWLEDGE_INDEX_MODE=persistent`，把 Chroma 与 manifest 持久化在 `data/runtime/knowledge/`。显式设置为 `memory` 时，Chroma 与 manifest 只保留在当前进程，并在每次启动时从 `data/reference/` 与 `data/runtime/memories/` 全量重建；Memory JSON 等业务源数据仍按原路径持久化。

诊断日志默认写入 `data/logs/`，由 `LOG_DIR` 和 `LOG_LEVEL` 控制。旧的 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 是保留的历史用户数据；production 不读取、不改写、不迁移、不删除这些目录。

## 开发验证

在项目环境中运行：

```powershell
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```
