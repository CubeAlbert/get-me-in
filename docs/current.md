# 当前状态

**当前阶段：** 当前基线多语言 UI／模型回复语言专项 L5 工程验证已完成，等待真实 provider／TTY smoke；R9 仍未授权

**当前任务：** 按 [`docs/multilingual-support.md`](multilingual-support.md) 完成 L5 真实 provider／TTY 矩阵，再进入 L6 用户审查与文档收口

**当前子任务：** L5 工程验证已完成：定向 151/151、完整 340/340、compileall、diff-check、静态 contract 和 fake/headless component smoke 通过；真实 provider／TTY smoke 待用户执行。

**当前阻塞：** 等待用户在 Windows 真实 TTY 执行 zh-CN／en-US provider smoke；自动化与 fake LLM 不能替代该证据。R9 仍需独立授权，未授权前不检查、设计或实施 R9。

**会话交接说明：** 决策 284 与 `docs/multilingual-support.md` 固定首版只支持 `zh-CN`／`en-US`，以 `UI_LOCALE`、`MODEL_RESPONSE_LANGUAGE` 两个进程级语义分别控制 UI 和模型回复；UI 使用 strict JSON catalog loader、stable key 和命名占位符，模型新增独立 `06_response_language.md`，不复制 system prompt。L1～L4 各自独立 checkpoint，L5 完整验证／真实 provider／TTY，L6 用户审查与收口。禁止新增 `/language`、自动检测、Session locale／schema、Memory build、embedding／Chroma、Input／Output schema、ModelMessageCodec、依赖、数据迁移或 R9 工作。当前 production Memory 已完成英文技术栈与英文年龄查询中文事实的真实检索对照，均正确 Top-1；该证据不替代英文真实模型 `query_memory` smoke。四个 legacy 数据目录仍不得读取、改写、迁移或删除。

**下一步：** 用户执行并反馈 L5 真实 provider／TTY 矩阵：zh-CN 与 en-US 的 finish、tool call、thinking、selection、approval、Main→Resume→Main；en-US 另验证一次真实 `query_memory` 并用英文回答，不触发 Memory build。通过后再实施 L6 收口，不得进入 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

289. **完成多语言专项 L5 工程验证并等待真实 provider／TTY smoke** — 定向 151/151、完整 unittest 340/340、compileall、diff-check、locale／Prompt 静态 contract 和 fake/headless component smoke 通过；真实 provider／Windows TTY 矩阵仍待用户证据，L6 尚未开始，R9 仍未授权。
288. **完成多语言专项 L4 ResponseLanguage Prompt 注入** — `06_response_language.md`、PromptRenderer 和 bootstrap Main／Resume 共享 resolved response locale 已由代码／测试提交 `8dc56a5` 完成；340 项 unittest、compileall、diff-check、Prompt 静态 contract 和精确白名单审查通过；进入 L5 验证，R9 仍未授权。
287. **完成多语言专项 L3 typed 固定事件文案与审批** — `ProgressKind`、canonical `tool_name`、CLI stable-key 投影和双语文案已由代码／测试提交 `cfca149` 完成；338 项 unittest、compileall、diff-check 和精确白名单审查通过；下一步实施 L4，R9 仍未授权。
286. **完成多语言专项 L2 CLI-owned UI 本地化** — Renderer、InputController、CommandRegistry、CliApp、WorkerRunner 和 application result presentation 已由代码／测试提交 `a868252` 完成；338 项 unittest、compileall、diff-check 和精确白名单审查通过；按门禁停在 L3 前，R9 仍未授权。
285. **完成多语言专项 L1 并进入 L2** — Locale、strict catalog loader、双语 catalog、Settings 语言配置和 bootstrap 诊断已由代码／测试提交 `21ccef3` 完成；用户批准将仅含必填 Settings fixture 迁移的 `tests/get_me_in/test_bootstrap.py` 纳入 L1 白名单；333 项 unittest、compileall 和 diff-check 通过，文档 checkpoint 与代码提交分离，R9 仍未授权。
284. **建立多语言 UI 与模型回复语言专项计划并留待新会话实施** — 首版固定 `zh-CN`／`en-US`、strict locale loader／命名占位符和单一 ResponseLanguage Prompt，按 L1～L6 实施；不增加运行时切换、Session／Memory／RAG／schema 变更，也不构成 R9 授权。
283. **完成 Knowledge 取消作用域修复 K5 最终收口** — 用户确认普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 `/exit` 三项真实终端测试无问题；五份核心文档已收口并删除临时计划，R9 仍未授权。
282. **完成 Knowledge 取消作用域修复 K4 验证并等待用户审查** — 完整 unittest 325/325、compileall、diff-check 通过；production composition 普通 Runtime 取消、`/ragreload` 取消／重试和 prepare 中 exit teardown 均通过，物理 TTY Esc 待用户复核，R9 仍未授权。
281. **完成 Knowledge 取消作用域修复 K1～K3** — `Application` 按命令维护实例级 active cancellation target；Knowledge 区分 prepare cancellation 与真实 failure，保留可查询状态并支持重试；定向回归 65/65 通过，K4 工程与真实 smoke 待完成，R9 仍未授权。
280. **建立 Knowledge 命令作用域取消修复计划** — 普通 Runtime Esc 不得取消后台 startup reload；`/ragreload` 继续可取消；Knowledge 区分 cancellation 与真实 failure，保持公开 API、数据路径和 R9 门禁不变，按 K1～K4 留待新会话实施。
