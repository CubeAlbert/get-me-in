# 当前状态

**当前阶段：** R8 已完成并通过最终用户审查；运行配置硬编码外置专项 E0～E5 已完成，等待用户审查，不进入 R9；R9 仍未授权

**当前任务：** 运行配置硬编码外置专项文档审查

**当前子任务：** E0～E4 已完成；E3 代码／测试 checkpoint 为 `154ff4f`，E4 完整门禁通过；E5 文档收口已完成，等待用户审查。

**当前阻塞：** 等待用户审查专项完成态；R9 独立授权门禁仍保持关闭。

**会话交接说明：** 决策 274 固定“运行参数外置、协议／安全不变量留在代码”的范围；E0～E5 已完成，代码／测试 checkpoint 为 `154ff4f`，文档与验证证据均已同步。E2 checkpoint 订正了 production 白名单，新增 `memory_service.py`，`retrieval.py` 保持原白名单位置；E3 未改变 Tool schema、数据边界或 R9 门禁。不输出 `.env` 值、不接入四个 legacy 数据目录。

**下一步：** 用户审查专项完成态；审查通过后仍需另行授权才可进入 R9。

**决策记录说明：** `current.md` 仅保留最近 10 条决策摘要；更早决策及完整正文请查阅 [`docs/decision.md`](decision.md)。以下按编号从新到旧排列。

276. **完成运行配置外置 E0～E5** — E3 代码／测试 checkpoint `154ff4f`；完整 unittest 318/318、compileall、diff-check、57/57 `.env` key/shape、退出码 2 配置错误、legacy refusal、persistent／memory 组件与 headless 根入口 smoke 通过；文档已收口，等待用户审查，R9 仍未授权。
275. **完成运行配置外置 E2 并订正 production 白名单** — E2 代码／测试 checkpoint `b424b62`，完整 unittest 313/313、compileall、diff-check 和旧硬编码静态扫描通过；`retrieval.py` 沿用既有白名单，新增 `memory_service.py` 仅接收并使用注入的日志文件名；R9 仍未授权。
274. **建立运行配置硬编码外置专项计划并留待新会话实施** — 固定运行配置与代码不变量分界、canonical `.env.example`、Settings fail-fast、legacy path refusal、白名单、E0～E5 checkpoint 和验证门禁；当前会话不实施，R9 仍未授权。
