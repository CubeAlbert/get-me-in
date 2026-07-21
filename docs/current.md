# 当前状态

**当前阶段：** M5: 简历 Agent

**当前任务：** 记忆集成（M5-5）— ✅ 全部完成

**当前子任务：** M5-5 全部子任务已终结（通用基础设施 ✅ + 简历专项 ⛔）。M5-8 Esc 中断基础功能 ✅ 完成（即时中止 📌 暂缓）。简历专项记忆（版本写入/历史检索）不予实现——ResumeAgent 通过 `query_memory` 工具即可获取用户个人信息和偏好。

**当前阻塞：** 无

**下一步：** 用户决定：① M4-6 InterviewAgent（⬜） ② 新阶段 ③ 其他

**已暂缓：** schema-based 填充工具

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
129. **`/rewind` 命令 + ↑↓ 输入历史** — 回退到历史输入点：select 选择 → `_pending_prefill` 预填到 CLI → 确认后截断 `_history`；纯内存操作不涉及文件存储；↑↓ 键导航输入历史（通过 `prompt_toolkit.KeyBindings` + `~has_completions` filter 与 autocomplete 下拉互斥）；预填机制 `_pending_prefill` 可复用于后续输入历史功能
130. **Esc 中断 Agent 处理** — 按 Esc 中断 agent loop：`_cancel_event` (`threading.Event`) + `_check_esc_pressed()` 跨平台非阻塞检测 + 三个检查点（while 开始/LLM 返回后/工具执行前）；工具执行前取消时注入合成 TOOL_CALL_RESULT(`__cancelled__`) 保证 history 闭环；即时中止（httpx transport close）暂缓，需 LLMClient 重构时纳入设计。详见 `docs/design.md#417-agent-中断机制` 和 decision #130
131. **记忆集成基础设施** — `AUTO_MEMORY_ON_EXIT` 配置项控制 Agent FINISH 时是否自动异步写入记忆（默认 false，守护线程不阻塞）；`/build-memory` CLI 命令手动触发记忆构建（异步）；`write_memory()` 目录名修正为 `_get_agent_key()`（main/resume/job_search）替代 `_get_agent_name()`（中文显示名）；3 文件共 ~15 行改动
132. **LLM 调用超时 + 异常处理** — OpenAI SDK 默认 600s 超时过长，新增 `LLM_TIMEOUT` 配置项（默认 60s）；`Exception` 捕获层：`BaseAgent.process()` 首轮 LLM 失败 pop 未消费 USER_INPUT 回滚 + `_process_with_spinner` daemon 线程兜底防 spinner 卡死；两处均返回 FINISH(error) 交还 CLI 控制权
133. **Spinner 计时排除 UIBridge 等待时长** — `_process_with_spinner` 中 spinner 的 elapsed 计时包含 `_handle_bridge_request` 等待用户选择/确认的时间。修复：新增 `paused_duration` 累计暂停时长，进入 UI 交互前记录 `pause_start`，退出后累加差值，elapsed 计算减去累计暂停时长。3 行改动，不改结构。
134. **SessionId 统一 — SaveManager & dumper 共享会话 ID** — 新建 `src/utils/session.py`（模块级单例，`init_session_id()` / `get_session_id()`）；`main.py` 启动时初始化；`SaveManager.__init__` 改用 `get_session_id()`；setter 内同步 `init_session_id(value)` 支持 `/restore`；`dumper.py` 移除独立的 `datetime.now()`，`/dump` 同 session 多次调用覆盖同一文件
135. **发送 LLM 消息剥离 thinking + 修正 input format role** — `_to_openai()` 中用 `dataclasses.replace(m, thinking=None)` 剥离 thinking 后再序列化发送，避免前轮推理过程浪费 token 和干扰模型；`08_input_format.md` 的 `role` 从 `"const": "user"` 修正为 `enum: ["user", "assistant", "system"]`，`event_type` 扩展 `tool_call`/`finish`，与实际发送数据一致
136. **不暴露 LLM 原生 reasoning_content** — DeepSeek API 原生 `reasoning_content` 可能包含系统提示词片段，暴露给用户有 prompt injection 风险。保持 LLM JSON 手写 `thinking` 方案，`LLMClient` 层不捕获原生推理字段。详见 decision.md #136。
