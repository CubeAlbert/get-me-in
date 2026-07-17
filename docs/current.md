# 当前状态

**当前阶段：** M5: 简历 Agent

**当前任务：** 会话状态管理（M5-7）— Rollback

**当前子任务：** 回滚到上句话（每次 FINISH 全量快照，支持回退到前一状态）

**当前阻塞：** 无

**下一步：** 设计 rollback 机制：如何触发回滚（CLI 命令？自动？），回滚后如何处理当前未保存的修改

**已暂缓：** schema-based 填充工具、记忆集成

**参考文档：** `docs/file-reader-design.md` — workspace 工具组完整设计；`data/resume/template/README.md` — 模板操作手册

**重要决策：** (编号，不记录日期 —— 发生重要决策时及时记录)
1-100: 见 decision.md
101-115: 见 decision.md
116-122: 见 decision.md
123. **会话状态管理模块** — `src/utils/saver.py` + `SaveManager`，auto-save on FINISH → `data/save/{session_id}/`，`/restore` 命令恢复，plan 随 session.json 持久化，延迟 sub 清理防崩溃丢数据，为 rollback 预留全量覆盖写入
124. **RAG 模型加载本地缓存优先** — Embedder/Reranker 先 `local_files_only=True` 纯本地加载，缓存未命中回退联网下载
125. **plan_status 落地到 Message 对象** — 在 `process()` 每次 append 消息时 stamp `plan_to_simple()` 到 `Message.plan_status`；TOOL_CALL_RESULT 也携带
126. **Restore 上下文预览** — choice title 追加 preview 文本；恢复后渲染最近 5 条消息面板
127. **plan_status 简化 schema** — 从完整 `PlanStatusInfo` 改为字符串格式 `{current: "序号|任务", completed: [...], remaining: [...]}`
128. **replan 工具** — 新增 `replan`（`plan_tools.py` 第 4 个工具）：保留已完成项、替换未完成项；强调状态变化必须先 `update_plan_status` 再继续
