# 当前状态

**当前阶段：** 当前基线多语言 UI／模型回复语言专项 L0 规划已完成；本会话不 coding，L1～L6 已获准留待新会话实施；R9 仍未授权

**当前任务：** 按 [`docs/multilingual-support.md`](multilingual-support.md) 在新会话实施 `zh-CN`／`en-US` UI locale loader、CLI 本地化和统一 ResponseLanguage Prompt 注入

**当前子任务：** L0 文档计划完成；代码尚未开始。新会话从 L1 Locale／catalog loader／Settings 开始，不得跳过白名单和 checkpoint。

**当前阻塞：** 无工程阻塞；用户要求本会话不得 coding。R9 仍需独立授权，未授权前不检查、设计或实施 R9。

**会话交接说明：** 决策 284 与 `docs/multilingual-support.md` 固定首版只支持 `zh-CN`／`en-US`，以 `UI_LOCALE`、`MODEL_RESPONSE_LANGUAGE` 两个进程级语义分别控制 UI 和模型回复；UI 使用 strict JSON catalog loader、stable key 和命名占位符，模型新增独立 `06_response_language.md`，不复制 system prompt。L1～L4 各自独立 checkpoint，L5 完整验证／真实 provider／TTY，L6 用户审查与收口。禁止新增 `/language`、自动检测、Session locale／schema、Memory build、embedding／Chroma、Input／Output schema、ModelMessageCodec、依赖、数据迁移或 R9 工作。当前 production Memory 已完成英文技术栈与英文年龄查询中文事实的真实检索对照，均正确 Top-1；该证据不替代英文真实模型 `query_memory` smoke。四个 legacy 数据目录仍不得读取、改写、迁移或删除。

**下一步：** 新会话执行 `/project-bootstrap`，读取本文件、四份核心活跃文档和 `docs/multilingual-support.md`，复核干净／已有工作树与 L1 白名单后只实施 L1；完成定向验证和独立 checkpoint 后再进入 L2。不得在本会话 coding，也不得进入 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

284. **建立多语言 UI 与模型回复语言专项计划并留待新会话实施** — 首版固定 `zh-CN`／`en-US`、strict locale loader／命名占位符和单一 ResponseLanguage Prompt，按 L1～L6 实施；不增加运行时切换、Session／Memory／RAG／schema 变更，也不构成 R9 授权。
283. **完成 Knowledge 取消作用域修复 K5 最终收口** — 用户确认普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 `/exit` 三项真实终端测试无问题；五份核心文档已收口并删除临时计划，R9 仍未授权。
282. **完成 Knowledge 取消作用域修复 K4 验证并等待用户审查** — 完整 unittest 325/325、compileall、diff-check 通过；production composition 普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 exit teardown 均通过，物理 TTY Esc 待用户复核，R9 仍未授权。
281. **完成 Knowledge 取消作用域修复 K1～K3** — `Application` 按命令维护实例级 active cancellation target；Knowledge 区分 prepare cancellation 与真实 failure，保留可查询状态并支持重试；定向回归 65/65 通过，K4 工程与真实 smoke 待完成，R9 仍未授权。
280. **建立 Knowledge 命令作用域取消修复计划** — 普通 Runtime Esc 不得取消后台 startup reload；`/ragreload` 继续可取消；Knowledge 区分 cancellation 与真实 failure，保持公开 API、数据路径和 R9 门禁不变，按 K1～K4 留待新会话实施。
279. **迁移当前运行数据目录并移除版本路径标识** — 当前生产基线不再使用版本身份标签；配置、测试、活跃文档和现有运行数据统一迁移到 `data/runtime/`，`.gitignore` 同步更新；四个 legacy 数据目录保持隔离，R9 仍未授权。
278. **收敛三份已完成专项文档并迁移 D1～D7 台账** — 用户确认运行配置专项完成；删除 Chroma、质量加固与运行配置三份专项执行文档，将仍暂缓的 D1～D7 完整迁入 `docs/task.md`，修正 `AGENTS.md` 活跃文档路由；历史由 Git 与既有决策保存，R9 仍未授权。
277. **完成运行配置审查 P1/P2 修复** — `459b1cf` 统一拒绝六个时长／轮询变量的非有限值，并让 Settings／logging setup 跨平台拒绝 `/`、`\\`；新增 18 项非有限值断言并补充路径分隔符覆盖，完整 unittest 320/320 通过，R9 仍未授权。
276. **完成运行配置外置 E0～E5** — E3 代码／测试 checkpoint `154ff4f`；完整 unittest 318/318、compileall、diff-check、57/57 `.env` key/shape、退出码 2 配置错误、legacy refusal、persistent／memory 组件与 headless 根入口 smoke 通过；文档已收口，等待用户审查，R9 仍未授权。
275. **完成运行配置外置 E2 并订正 production 白名单** — E2 代码／测试 checkpoint `b424b62`，完整 unittest 313/313、compileall、diff-check 和旧硬编码静态扫描通过；`retrieval.py` 沿用既有白名单，新增 `memory_service.py` 仅接收并使用注入的日志文件名；R9 仍未授权。
