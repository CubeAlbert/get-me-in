# 旧入口可运行基线

> 适用分支：`refactor`。本文记录 R0 阶段旧入口的源码基线和已观察到的启动行为，为 R8 切换 `main.py` 前保留可追溯的回退点。本文不表示 v2 必须复用旧启动链路。

## 1. 基线提交

| 项目 | 值 |
|---|---|
| 旧入口 | `main.py` → `main()` |
| 源码基线提交 | `f5ee3765cc055622029d8ce34c1a8f611202c434` |
| 源码基线说明 | `fix(agent): strip thinking field from history messages before API serialization` |
| 基线确认日期 | 2026-07-21 |
| 当前 `refactor` 与该提交的 `main.py`、`src/` 差异 | 无 |
| 启动命令 | `uv run python main.py` |

后续 R0 文档提交没有修改 `main.py` 或 `src/`，因此上述提交仍准确代表当前分支的旧入口源码。R8 切换入口时应将 `main.py` 修改单独提交，使本提交和 v1 入口可直接作为回退参照。

## 2. 已观察的启动链路

旧入口的顺序如下：

1. `src.config` 加载 `.env` 并校验配置。
2. 初始化 session id。
3. 调用 `src.rag.start()`，启动 RAG 模型／索引加载。
4. 获取 LLM client，加载 PromptLoader，注册 JobSearchAgent 和 ResumeAgent。
5. 创建 MainAgent 和 `App`，进入 CLI 输入循环。
6. 退出后调用 lifecycle shutdown。

## 3. 本次验证记录

| 验证项 | 结果 | 证据／说明 |
|---|---|---|
| `uv run python main.py` 可完成依赖解析和配置加载 | 通过 | 日志显示 `.env` 加载与必填环境变量校验通过 |
| 旧入口可初始化 LLM client | 通过 | 日志显示“LLM 客户端初始化完成” |
| RAG 在 CLI 前加载 | 已确认 | 进程在模型／索引加载期间持续运行，尚未到达可交互提示 |
| 实际进入并退出交互 CLI | 未在本轮自动验证 | 受控终端无法替代用户终端；为避免持续模型下载／加载，已终止本次启动的项目 Python 进程 |

## 4. 结论与 R8 约束

- 旧入口源码基线已固定为 `f5ee3765cc055622029d8ce34c1a8f611202c434`。
- 当前启动顺序将 RAG 初始化置于 CLI 前；缺少本地模型缓存或网络受限时，首次进入交互提示会延迟。这是旧实现行为，也是 R5/R6 拆分 CLI 与 Knowledge 生命周期时需要消除的耦合。
- 完整人工验证仍应按 [legacy-cli-smoke-checklist.md](legacy-cli-smoke-checklist.md) 的 C01 和 C05 在可交互终端完成；该验证不应阻塞 R0 的架构基线记录，但 G0 审查必须如实保留其“未执行”状态。
- v2 允许将模型加载与 CLI 可用性解耦，但必须在对应 R5/R6 验收中明确 loading、error 和 retry 的可见行为。
