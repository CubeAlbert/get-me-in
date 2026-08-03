# 当前状态

**当前阶段：** 当前基线多语言 UI／模型回复语言专项 L1～L6 已完成并收口；R9 仍未授权

**当前任务：** 多语言专项已完成；如继续开发，须先获得 R9 独立授权并重新执行前置 Review

**当前子任务：** L1～L6 已完成：定向 151/151、完整 346/346、compileall、diff-check、静态 contract、fake/headless component smoke 和用户确认的双语言真实 provider／Windows TTY 体验通过；代码／测试审查修复 checkpoint 为 `02c9c5d`，文档 checkpoint 已完成。

**当前阻塞：** 当前专项无阻塞。R9 仍需独立授权，未授权前不检查、设计或实施 R9。

**会话交接说明：** 决策 284 与当前核心文档固定首版只支持 `zh-CN`／`en-US`，以 `UI_LOCALE`、`MODEL_RESPONSE_LANGUAGE` 两个进程级语义分别控制 UI 和模型回复；缺失时分别默认为 `zh-CN`、`ui`（随中文 UI 解析为 `zh-CN`），`LOCALES_DIR` 默认为 `data/locales`。UI 使用 strict JSON catalog loader、stable key 和命名占位符，模型使用独立 `07_response_language.md`，并按 `08_input_format.md`、`09_output_format.md`、`10_reserved.md` 顺序拼接，不复制 system prompt。L1～L4 各自独立 checkpoint，L5 完整验证／真实 provider／TTY，L6 用户审查与收口。禁止新增 `/language`、自动检测、Session locale／schema、Memory build、embedding／Chroma、Input／Output schema、ModelMessageCodec、依赖、数据迁移或 R9 工作。当前 production Memory 已完成英文技术栈与英文年龄查询中文事实的真实检索对照，均正确 Top-1；该证据不替代英文真实模型 `query_memory` smoke。四个 legacy 数据目录仍不得读取、改写、迁移或删除。

**下一步：** 若继续工作，先请求 R9 前置 Review 授权；在此之前不进入 R9，不读取或改写四个 legacy 数据目录。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

293. **合并多语言专项最终事实并删除已完成执行文档** — 删除已完成的 `docs/multilingual-support.md`，移除核心文档中的活跃链接和保留措辞；当前架构、配置、边界、验证与 R9 门禁继续由 README、五份核心文档、Git 和决策 284～292 保存。
292. **完成多语言专项 L6 收口并保留专项文档** — 用户确认双语言真实 provider／Windows TTY 体验无大问题；代码／测试审查修复提交 `02c9c5d`，完整 unittest 346/346、compileall、diff-check 通过；README、五份核心文档和本决策记录完成收口；专项文档当时按用户要求保留，后由决策 293 授权删除。
291. **重排 general_agent Prompt 文件编号** — `06_response_language`、`07_input_format`、`08_output_format`、`09_reserved` 依次改为 `07`、`08`、`09`、`10`；PromptRenderer 仍按文件名排序，`render_output_format()` 仍按唯一 suffix 发现；代码／测试提交 `c4ac8dd`，全量 unittest 341/341 通过。
290. **补充多语言 Settings 中文默认值** — `UI_LOCALE` 缺失默认为 `zh-CN`，`MODEL_RESPONSE_LANGUAGE` 缺失默认为 `ui` 并解析为中文，`LOCALES_DIR` 缺失默认为 `data/locales`；`.env.example` 已注释可用选项，代码／测试提交 `a5efaa1`，全量 unittest 341/341 通过。
289. **完成多语言专项 L5 工程验证并等待真实 provider／TTY smoke** — 定向 151/151、完整 unittest 340/340、compileall、diff-check、locale／Prompt 静态 contract 和 fake/headless component smoke 通过；真实 provider／Windows TTY 矩阵仍待用户证据，L6 尚未开始，R9 仍未授权。
288. **完成多语言专项 L4 ResponseLanguage Prompt 注入** — `06_response_language.md`、PromptRenderer 和 bootstrap Main／Resume 共享 resolved response locale 已由代码／测试提交 `8dc56a5` 完成；340 项 unittest、compileall、diff-check、Prompt 静态 contract 和精确白名单审查通过；进入 L5 验证，R9 仍未授权。
287. **完成多语言专项 L3 typed 固定事件文案与审批** — `ProgressKind`、canonical `tool_name`、CLI stable-key 投影和双语文案已由代码／测试提交 `cfca149` 完成；338 项 unittest、compileall、diff-check 和精确白名单审查通过；下一步实施 L4，R9 仍未授权。
286. **完成多语言专项 L2 CLI-owned UI 本地化** — Renderer、InputController、CommandRegistry、CliApp、WorkerRunner 和 application result presentation 已由代码／测试提交 `a868252` 完成；338 项 unittest、compileall、diff-check 和精确白名单审查通过；按门禁停在 L3 前，R9 仍未授权。
285. **完成多语言专项 L1 并进入 L2** — Locale、strict catalog loader、双语 catalog、Settings 语言配置和 bootstrap 诊断已由代码／测试提交 `21ccef3` 完成；用户批准将仅含必填 Settings fixture 迁移的 `tests/get_me_in/test_bootstrap.py` 纳入 L1 白名单；333 项 unittest、compileall 和 diff-check 通过，文档 checkpoint 与代码提交分离，R9 仍未授权。
284. **建立多语言 UI 与模型回复语言专项计划并留待新会话实施** — 首版固定 `zh-CN`／`en-US`、strict locale loader／命名占位符和单一 ResponseLanguage Prompt，按 L1～L6 实施；不增加运行时切换、Session／Memory／RAG／schema 变更，也不构成 R9 授权。
