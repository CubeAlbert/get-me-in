# 当前状态

**当前阶段：** 当前基线 Knowledge 取消作用域修复 K1～K4 已完成，正在等待用户审查真实 smoke 后收口；R8 及既有 R9 前专项仍保持完成，R9 未授权

**当前任务：** 按 `docs/knowledge-cancellation-scope-fix.md` 修复前台取消误伤后台 Knowledge startup reload 的问题

**当前子任务：** K5——用户审查 production composition smoke；确认后收口五份核心文档并删除临时专项计划。

**当前阻塞：** 等待用户审查真实 smoke；物理 TTY Esc 尚未由本终端独立证明，R9 仍未取得独立授权。

**会话交接说明：** 决策 280 与 `docs/knowledge-cancellation-scope-fix.md` 记录本次缺陷和实施边界；K1～K4 已按文件白名单完成，定向回归 65/65、完整 unittest 325/325、compileall、diff-check 和三组 production composition smoke 通过。普通 Runtime 取消后 Knowledge 为 `ready/succeeded`；`/ragreload` 取消后可重试；prepare 中 exit teardown 为 `CANCELLED` 且 worker 停止。物理 TTY Esc 待用户复核；四个 legacy 数据目录仍不得读取、改写、迁移或删除，本修复不构成 R9 授权。

**下一步：** 请审查三组 production composition smoke，并在需要时用真实 TTY 复核物理 Esc；确认后再更新 design/plan/task/current/decision、删除临时专项计划并提交文档收口。不得借本修复检查、设计或实施 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

282. **完成 Knowledge 取消作用域修复 K4 验证并等待用户审查** — 完整 unittest 325/325、compileall、diff-check 通过；production composition 普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 exit teardown 均通过，物理 TTY Esc 待用户复核，R9 仍未授权。
281. **完成 Knowledge 取消作用域修复 K1～K3** — `Application` 按命令维护实例级 active cancellation target；Knowledge 区分 prepare cancellation 与真实 failure，保留可查询状态并支持重试；定向回归 65/65 通过，K4 工程与真实 smoke 待完成，R9 仍未授权。
280. **建立 Knowledge 命令作用域取消修复计划** — 普通 Runtime Esc 不得取消后台 startup reload；`/ragreload` 继续可取消；Knowledge 区分 cancellation 与真实 failure，保持公开 API、数据路径和 R9 门禁不变，按 K1～K4 留待新会话实施。
279. **迁移当前运行数据目录并移除版本路径标识** — 当前生产基线不再使用版本身份标签；配置、测试、活跃文档和现有运行数据统一迁移到 `data/runtime/`，`.gitignore` 同步更新；四个 legacy 数据目录保持隔离，R9 仍未授权。
278. **收敛三份已完成专项文档并迁移 D1～D7 台账** — 用户确认运行配置专项完成；删除 Chroma、质量加固与运行配置三份专项执行文档，将仍暂缓的 D1～D7 完整迁入 `docs/task.md`，修正 `AGENTS.md` 活跃文档路由；历史由 Git 与既有决策保存，R9 仍未授权。
277. **完成运行配置审查 P1/P2 修复** — `459b1cf` 统一拒绝六个时长／轮询变量的非有限值，并让 Settings／logging setup 跨平台拒绝 `/`、`\\`；新增 18 项非有限值断言并补充路径分隔符覆盖，完整 unittest 320/320 通过，R9 仍未授权。
276. **完成运行配置外置 E0～E5** — E3 代码／测试 checkpoint `154ff4f`；完整 unittest 318/318、compileall、diff-check、57/57 `.env` key/shape、退出码 2 配置错误、legacy refusal、persistent／memory 组件与 headless 根入口 smoke 通过；文档已收口，等待用户审查，R9 仍未授权。
275. **完成运行配置外置 E2 并订正 production 白名单** — E2 代码／测试 checkpoint `b424b62`，完整 unittest 313/313、compileall、diff-check 和旧硬编码静态扫描通过；`retrieval.py` 沿用既有白名单，新增 `memory_service.py` 仅接收并使用注入的日志文件名；R9 仍未授权。
274. **建立运行配置硬编码外置专项计划并留待新会话实施** — 固定运行配置与代码不变量分界、canonical `.env.example`、Settings fail-fast、legacy path refusal、白名单、E0～E5 checkpoint 和验证门禁；当前会话不实施，R9 仍未授权。
273. **移除旧 RAG 环境变量兼容别名** — 代码／测试 `df01327` 已 checkpoint；`.env.example` 与 Settings 不再支持 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE`，正式变量和既有默认值保持不变，完整 unittest 306/306 通过，R9 仍未授权。
