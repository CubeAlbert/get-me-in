# 当前状态

**当前阶段：** 当前基线 Knowledge 取消作用域修复 K1～K5 已完成；全部已授权的 R9 前工作保持完成，等待 R9 独立授权，R9 未授权

**当前任务：** Knowledge 取消作用域修复已完成；保持当前生产基线，等待后续独立授权

**当前子任务：** 无；K1～K5 已完成，未取得独立授权前不启动 R9。

**当前阻塞：** 无当前实施阻塞；R9 仍需独立授权，未授权前不检查、设计或实施 R9。

**会话交接说明：** 决策 280～283 记录本次缺陷、实施边界、K1～K4 验证和 K5 用户复核；K1～K5 已按文件白名单完成，定向回归 65/65、完整 unittest 325/325、compileall、diff-check、真实 Chroma smoke、三组 production composition smoke 与用户确认的三项真实终端测试均通过。普通 Runtime 取消后 Knowledge 为 `ready/succeeded`；`/ragreload` 取消后可重试；prepare 中 exit teardown 为 `CANCELLED` 且 worker 停止。四个 legacy 数据目录仍不得读取、改写、迁移或删除，本修复不构成 R9 授权。

**下一步：** 等待 R9 独立授权；在获得授权前不得检查、设计或实施 R9，也不得扩大本次修复边界。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

283. **完成 Knowledge 取消作用域修复 K5 最终收口** — 用户确认普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 `/exit` 三项真实终端测试无问题；五份核心文档已收口并删除临时计划，R9 仍未授权。
282. **完成 Knowledge 取消作用域修复 K4 验证并等待用户审查** — 完整 unittest 325/325、compileall、diff-check 通过；production composition 普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 exit teardown 均通过，物理 TTY Esc 待用户复核，R9 仍未授权。
281. **完成 Knowledge 取消作用域修复 K1～K3** — `Application` 按命令维护实例级 active cancellation target；Knowledge 区分 prepare cancellation 与真实 failure，保留可查询状态并支持重试；定向回归 65/65 通过，K4 工程与真实 smoke 待完成，R9 仍未授权。
280. **建立 Knowledge 命令作用域取消修复计划** — 普通 Runtime Esc 不得取消后台 startup reload；`/ragreload` 继续可取消；Knowledge 区分 cancellation 与真实 failure，保持公开 API、数据路径和 R9 门禁不变，按 K1～K4 留待新会话实施。
279. **迁移当前运行数据目录并移除版本路径标识** — 当前生产基线不再使用版本身份标签；配置、测试、活跃文档和现有运行数据统一迁移到 `data/runtime/`，`.gitignore` 同步更新；四个 legacy 数据目录保持隔离，R9 仍未授权。
278. **收敛三份已完成专项文档并迁移 D1～D7 台账** — 用户确认运行配置专项完成；删除 Chroma、质量加固与运行配置三份专项执行文档，将仍暂缓的 D1～D7 完整迁入 `docs/task.md`，修正 `AGENTS.md` 活跃文档路由；历史由 Git 与既有决策保存，R9 仍未授权。
277. **完成运行配置审查 P1/P2 修复** — `459b1cf` 统一拒绝六个时长／轮询变量的非有限值，并让 Settings／logging setup 跨平台拒绝 `/`、`\\`；新增 18 项非有限值断言并补充路径分隔符覆盖，完整 unittest 320/320 通过，R9 仍未授权。
276. **完成运行配置外置 E0～E5** — E3 代码／测试 checkpoint `154ff4f`；完整 unittest 318/318、compileall、diff-check、57/57 `.env` key/shape、退出码 2 配置错误、legacy refusal、persistent／memory 组件与 headless 根入口 smoke 通过；文档已收口，等待用户审查，R9 仍未授权。
275. **完成运行配置外置 E2 并订正 production 白名单** — E2 代码／测试 checkpoint `b424b62`，完整 unittest 313/313、compileall、diff-check 和旧硬编码静态扫描通过；`retrieval.py` 沿用既有白名单，新增 `memory_service.py` 仅接收并使用注入的日志文件名；R9 仍未授权。
274. **建立运行配置硬编码外置专项计划并留待新会话实施** — 固定运行配置与代码不变量分界、canonical `.env.example`、Settings fail-fast、legacy path refusal、白名单、E0～E5 checkpoint 和验证门禁；当前会话不实施，R9 仍未授权。
