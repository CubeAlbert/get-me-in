# get-me-in

面向程序员的 CLI AI 求职助手。生产运行使用 `src/get_me_in/` 下的 v2 架构，由 Main 路由 Agent 与 Resume 简历 Agent 协作完成当前已落地的求职能力。

## 运行入口

唯一生产入口是仓库根目录的 `main.py`：

```powershell
uv run python main.py
```

诊断时也可以调用同一套 v2 CLI 模块入口：

```powershell
uv run python -m src.get_me_in.cli
```

启动前将 `.env.example` 复制为 `.env`，填写 OpenAI-compatible 服务地址、密钥和模型名称。配置由 `Settings.from_env()` 解析；静态输入目录由项目固定提供，运行目录由 v2 配置提供。

## 当前能力

当前 production Catalog 包含 2 个 Agent：

- `Main`：统一入口和路由，只根据当前可用 SubAgent 清单识别需求、收集必要上下文并切换 Agent。
- `Resume`：处理简历模板复制、读取、编辑、替换、PDF 构建、打开和 PDF 合并等简历工作流。

当前 Catalog 由代码动态导出 26 个 `ToolDefinition`；工具可见性按 Agent capability 隔离，工具本身不构成额外的业务 Agent。真实数量以 `AgentCatalog.list_descriptors()` 与 `ToolCatalog.export_descriptors()` 为准。

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

命令名称、帮助文本和补全以 `CommandRegistry.help_entries()` 与 `CommandRegistry.completions()` 的实际结果为准；历史 `/auto-approve-switch` 不属于当前命令。

## 数据与配置边界

v2 复用的静态输入只有：

- `data/reference/`
- `data/prompts/`
- `data/resume/template/`

业务运行数据只写入：

- `data/workspace/`：工作区文件和会话可见的用户工作内容
- `data/v2/`：session、Knowledge、Memory、Artifact 等 v2 持久化数据

诊断日志默认写入 `data/logs/`，由 `LOG_DIR` 和 `LOG_LEVEL` 控制。旧的 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/` 是保留的历史用户数据；production v2 不读取、不改写、不迁移、不删除这些目录。

## 回退边界

紧急回退不得触碰旧运行数据：

- 在 R8-D 之后、R8-G 文档提交之前：先 `git revert 7514af3`，再 `git revert 9fbeabc`。
- R8-G 文档提交之后：先按逆序回退 R8-G 提交，再回退 `7514af3`，最后回退 `9fbeabc`。

只有 legacy 源码已经恢复后，才允许实际启用 legacy-only 配置。回退仅恢复代码和配置历史，不迁移或清理旧用户数据。

## 开发验证

在项目环境中运行：

```powershell
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```

R8-G 的完整根入口、真实 Knowledge／Memory／Artifact adapter、CLI 交互和旧数据拒绝访问验证，必须在独立 G8 验收中完成。
