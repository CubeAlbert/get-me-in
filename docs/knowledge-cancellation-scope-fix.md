# Knowledge 取消作用域修复计划

## 1. 状态与边界

- **状态：** 只读诊断与修改计划已完成；代码和测试尚未修改，留待新会话实施。
- **性质：** 当前生产基线缺陷修复，独立于 R9；本计划不检查、设计或实施 InterviewAgent Workflow。
- **数据边界：** 不读取、改写、迁移或删除 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/`；不再次迁移 `data/runtime/`。
- **接口边界：** 保持 `Application.request_cancel(reason)`、`WorkerRunner`、`KnowledgeService`、`RuntimeCommand`、`ApplicationCommand` 与 `RuntimeEvent` 的公开签名不变；不新增公开类、公开方法、命令、持久化字段或依赖。

## 2. 已确认问题

2026-08-03 11:18:26，后台 `load-knowledge` 开始执行 embedding／reranker 预热。前台普通 Runtime 调用随后被取消；`Application.request_cancel()` 同时调用 Session 与 Knowledge 的 `request_cancel()`，使仍处于 `LOADING` 的 `_reload_cancellation` 被置为 cancelled。embedding 模型在 11:19:11 完成构造后再次检查 token，于 `prepare()` 抛出 `InterruptedError("knowledge index operation cancelled")`。

当前 `KnowledgeService.reload()` 把该取消当作普通异常：Knowledge 进入 `ERROR` 并返回带 failure 的 `ReloadReport`。由于 `BackgroundWorker` 自己的 job token 没有被取消，它把返回值记录为 `FAILED`，形成用户看到的错误。

该异常发生在 manifest load 和 source scan 之前，因此不是 `data/v2/` → `data/runtime/` 路径迁移或索引内容损坏。最近的路径迁移提交也未修改 Application／Knowledge 的取消生命周期；问题来自既有的取消广播与 prepare 阶段异常处理缺口。

## 3. 目标契约

1. `Application.request_cancel()` 只取消当前由 `Application.handle(command)` 执行的前台操作。
2. 当前命令是 `RuntimeCommand` 时，只调用 `SessionService.request_cancel()`；不得取消后台 startup reload。
3. 当前命令是 `ReloadKnowledge` 时，只调用 `KnowledgeService.request_cancel()`；`/ragreload` 继续可由 Esc／Ctrl+C 取消。
4. `RestoreSession`、`RewindSession`、`ExitSubAgent`、`DumpSession`、`BuildMemory` 没有同步可取消阶段时，不广播取消到无关组件。
5. 后台 startup reload 只接受其 `BackgroundWorker` job token 的取消；`BackgroundWorker.close()` 仍负责关闭时的协作取消与有界等待。
6. `KnowledgeService.reload()` 必须区分取消与真实 prepare／adapter failure：
   - startup 在首次成功前被 worker 取消时，不把取消记录成生产故障；
   - 已有 `READY`／`DEGRADED` index 的显式 reload 被取消时，保留取消前的可查询状态；
   - 返回 typed cancellation failure 供前台命令展示，并允许后续 reload 重置 token 后重试；
   - 非取消异常仍进入 `ERROR` 或既有 partial-failure 状态并保留 traceback。
7. worker-owned token 被取消时，终态必须是 `BackgroundJobState.CANCELLED`；真实 failure 才是 `FAILED`。

## 4. 推荐实现

### K1 —— Application 前台取消作用域

- 在 `Application` 内增加实例级、锁保护的私有 active cancellation target；不得使用模块级状态或裸字符串协议。
- `handle(command)` 在进入实际分发前按 command 类型设置 target，并在 `finally` 中清除；跨线程 `request_cancel(reason)` 只读取并调用当前 target。
- `RuntimeCommand` 映射到 Session；`ReloadKnowledge` 映射到 Knowledge；其他 `ApplicationCommand` 映射为空。
- 后台 `knowledge.start()` 不经过 `Application.handle()`，因此不会成为前台取消目标。
- 保持 `WorkerRunner` 只调用公开 `Application.request_cancel()`，不让 CLI 识别 Knowledge 私有状态。

### K2 —— Knowledge 取消状态与日志语义

- 在 `reload()` 进入 `LOADING` 前保存可恢复的上一状态；startup 的恢复状态为 `IDLE`，显式 reload 优先恢复原 `READY`／`DEGRADED`，原为 `ERROR` 时保持 `ERROR`。
- 单独捕获 `InterruptedError`，记录 INFO／WARNING 级取消上下文并返回 typed failure，不使用 `logger.exception()` 记录 ERROR traceback。
- 保留普通异常的现有 ERROR traceback、重试 token reset、manifest pending/error 与 source partial failure 语义。
- 不修改 Chroma adapter 的取消检查点；prepare 前后检查仍是协作取消的必要边界。

### K3 —— 回归测试

- 普通 `RuntimeCommand` 执行期间调用 `Application.request_cancel()`：Session 收到一次取消，Knowledge 不收到取消。
- `ReloadKnowledge` 执行期间取消：Knowledge 收到一次取消，Session 不收到取消。
- `Application.handle()` 返回或异常后 active target 被清除；空闲取消不影响 startup Knowledge。
- startup 在 embedder／reranker `prepare()` 阶段收到 worker token 取消：Knowledge 不进入 `ERROR`，job 终态为 `CANCELLED`。
- `READY`／`DEGRADED` 状态下显式 reload 在 prepare 阶段取消：保留原可查询状态，报告取消，下一次 reload 成功。
- 真实 prepare failure 仍进入 `ERROR`、worker 仍为 `FAILED`；现有 index mutation cancellation、worker timeout 和 retry 测试继续通过。

### K4 —— 工程与真实行为验证

```powershell
uv run python -m unittest tests.get_me_in.test_bootstrap tests.get_me_in.test_knowledge_service tests.get_me_in.test_resources tests.get_me_in.test_cli_worker
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```

若默认 uv cache 再次出现权限拒绝，只为本次命令设置仓库内被忽略的可写 `UV_CACHE_DIR`，原样重跑，不修改全局缓存 ACL。

真实行为至少验证：

1. persistent 模式冷启动期间取消一条普通前台对话；后台 Knowledge 继续完成并进入 `READY`，日志中无 Knowledge ERROR／FAILED。
2. 执行 `/ragreload` 后按 Esc；命令可取消，已有 index 仍可查询，再次 `/ragreload` 可成功。
3. 模型 prepare 尚未完成时 `/exit`；worker 记录 `CANCELLED`，进程在配置的 shutdown timeout 内退出，无残留 Python 进程和 use-after-close。

真实 smoke 只使用当前 `data/runtime/`；不得以读取四个 legacy 数据目录来证明边界。

## 5. 文件白名单

代码／测试实施只允许修改：

- `src/get_me_in/application/application.py`
- `src/get_me_in/application/knowledge_service.py`
- `tests/get_me_in/test_bootstrap.py`
- `tests/get_me_in/test_knowledge_service.py`
- `tests/get_me_in/test_resources.py`（仅在补充 worker job-state 断言确有需要时）

`tests/get_me_in/test_cli_worker.py` 只运行回归，预期不修改。若实现需要修改 `WorkerRunner`、Chroma adapter、公开 API、domain/event、Settings、bootstrap、依赖或白名单外 production 文件，必须停止并重新确认设计。

## 6. 提交与停止门禁

1. K1／K2 与回归测试作为一个原子 code/test 修复提交；提交前检查 staged allowlist。
2. 完整自动化、compileall、diff-check 通过后再执行真实行为 smoke；工程验证不得冒充真实 TTY smoke。
3. 用户审查真实 smoke 后，更新 `docs/current.md`、`docs/design.md`、`docs/plan.md`、`docs/task.md`、`docs/decision.md`，并删除本临时专项计划；历史由 Git 与决策记录保存。
4. 修复完成和文档收口都不自动授权 R9；进入 R9 仍需独立指令。
