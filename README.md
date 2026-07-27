# get-me-in

面向程序员的 AI 求职助手。当前仓库正在从 legacy 架构受控迁移到 `src/get_me_in/` v2。

## 当前入口与观察期

当前生产入口仍是：

```powershell
uv run python main.py
```

在 R8 入口切换完成前，可用以下命令预览 v2 CLI：

```powershell
uv run python -m src.get_me_in.cli
```

`.env.example` 的 v2 配置与 `Settings.from_env()` 对齐。观察期内保留其中标记为 **legacy rollback only** 的变量，以便在根入口切换后可单独回退入口提交；v2 不读取这些变量。

## 数据边界

v2 直接使用以下静态输入：

- `data/reference/`
- `data/prompts/`
- `data/resume/template/`

v2 的运行数据写入显式的 `data/workspace/` 与 `data/v2/`。旧 `data/save/`、`data/memories/`、`data/chroma/` 与 `data/temp/` 是未迁移的历史用户数据：不读取、不改写、不迁移，也不删除。

## 回退边界

R8 观察期若入口验证未通过，只回退入口切换提交；不得触碰旧运行数据。遗留源码删除将在观察通过并经用户审查后才会执行。
