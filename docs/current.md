# 当前状态

**当前阶段：** R8 已完成并通过最终用户审查；运行配置硬编码外置专项 E0～E5 及审查 P1/P2 修复已完成，等待用户审查，不进入 R9；R9 仍未授权

**当前任务：** 运行配置硬编码外置专项审查修复复核

**当前子任务：** 已修复 P1 非有限时长／轮询值和 P2 跨平台日志文件名分隔符校验；代码／测试 checkpoint 为 `459b1cf`，完整 unittest 320/320 通过，等待复核。

**当前阻塞：** 等待用户审查专项完成态；R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 274 固定“运行参数外置、协议／安全不变量留在代码”的范围；E0～E5 已完成，审查发现的 P1/P2 已由 `459b1cf` 修复并验证。P1 覆盖六个时长／轮询变量的 `nan`、`inf`、`-inf`；P2 在 Settings 与 logging setup 统一拒绝 `/`、`\\`。不输出 `.env` 值、不接入四个 legacy 数据目录或进入 R9。

**下一步：** 用户复核 P1/P2 修复；通过后仍需另行授权才可进入 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

277. **完成运行配置审查 P1/P2 修复** — `459b1cf` 统一拒绝六个时长／轮询变量的非有限值，并让 Settings／logging setup 跨平台拒绝 `/`、`\\`；新增 18 项非有限值断言并补充路径分隔符覆盖，完整 unittest 320/320 通过，R9 仍未授权。
276. **完成运行配置外置 E0～E5** — E3 代码／测试 checkpoint `154ff4f`；完整 unittest 318/318、compileall、diff-check、57/57 `.env` key/shape、退出码 2 配置错误、legacy refusal、persistent／memory 组件与 headless 根入口 smoke 通过；文档已收口，等待用户审查，R9 仍未授权。
275. **完成运行配置外置 E2 并订正 production 白名单** — E2 代码／测试 checkpoint `b424b62`，完整 unittest 313/313、compileall、diff-check 和旧硬编码静态扫描通过；`retrieval.py` 沿用既有白名单，新增 `memory_service.py` 仅接收并使用注入的日志文件名；R9 仍未授权。
274. **建立运行配置硬编码外置专项计划并留待新会话实施** — 固定运行配置与代码不变量分界、canonical `.env.example`、Settings fail-fast、legacy path refusal、白名单、E0～E5 checkpoint 和验证门禁；当前会话不实施，R9 仍未授权。
273. **移除旧 RAG 环境变量兼容别名** — 代码／测试 `df01327` 已 checkpoint；`.env.example` 与 Settings 不再支持 `BI_ENCODER_MODEL`、`CROSS_ENCODER_MODEL`、`EMBED_BATCH_SIZE`，正式变量和既有默认值保持不变，完整 unittest 306/306 通过，R9 仍未授权。
272. **完成 Chroma memory／persistent 模式订正** — 计划 `e23aa4a`、代码／测试 `a5df705` 已 checkpoint；定向 72/72、完整 305/305、compileall、diff-check、真实双模式 smoke 与数据边界门禁通过，R9 仍未授权。
271. **确认并授权 Chroma memory／persistent 模式订正** — 默认保持 persistent；memory 使用 `EphemeralClient` 与 process-local manifest 成对装配并每次启动全量重建；旧 Chroma 路径继续隔离，按专项计划执行，不进入 R9。
270. **完成 tool call message 修正的真实 provider／TTY smoke 与最终收口** — `SHOW_THINKING=false`／`true` 两组工具调用均显示 message；关闭时无摘要，开启时 finish thinking 以纯文本 Panel 位于最终 Markdown message 上方；本修正全部完成，R9 仍未授权。
269. **完成 tool call message 修正的工程实现与自动化门禁** — `b190a06`、`0694c2b`、`5a43fda` 已提交；定向 65/65、84/84，完整 unittest 296/296、compileall、diff-check、InputFormat blob 与 production-component smoke 通过；等待真实 provider／TTY smoke，R9 仍未授权。
268. **确认 tool call message 非空契约与 CLI Markdown 展示修正** — 所有模型输出 message 由 parser 强制非空；finish thinking 仅在 Prompt 中必填且为纯文本；`ToolStarted` 携带 message/thinking，CLI 按 thinking Panel → Markdown message → 工具状态展示；范围与分片 checkpoint 已确认，R9 仍未授权。
