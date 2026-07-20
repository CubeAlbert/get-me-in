# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**get-me-in** — AI 求职助手，面向程序员的多 Agent 系统。CLI 交互，Python 3.14。

## Commands

```bash
uv run python main.py          # 启动 CLI
uv sync                        # 安装/同步依赖
uv add <pkg> / uv remove <pkg> # 添加/移除依赖
uv run --with jupyter --with jupyterlab-lsp --with jedi-language-server jupyter lab  # 交互式调试
```

CLI 命令：
- `/edit` — 长文本输入（调 `$EDITOR`）
- `/ragreload [关键词]` — 重载 RAG 索引
- `/dump` — 导出当前 Agent 对话历史到 `data/logs/`
- `/restore [session_id]` — 恢复存档会话（无参数交互选择）
- `/exit_sub` — 子 Agent 退回主 Agent
- `/exit` — 退出程序

## Workflow

本项目遵循 **Plan → Execute → Result Validation → Replan** 循环。
工作完成后应使用 `/project-checkpoint` 更新 `docs/current.md` 和 `docs/task.md`。
新会话开始时使用 `/project-bootstrap` 恢复上下文。
**不要主动推进项目进度** — 完成当前任务后，主动提醒用户审查成果并保存状态（`/project-checkpoint`），由用户决定是否继续下一步。

## Architecture

**Hub-and-Spoke 模式：** 主 Agent 是唯一入口和调度中心。所有 Agent 共享相同的基础能力（对话循环、意图识别、工具调用、记忆读写），主 Agent 唯一特权是持有 `AgentRegistry` 调度子 Agent。子 Agent 之间不允许直接通信，也不允许持有或调度其他 Agent。

**App 双循环结构：**
```
外层 while input():                    ← 等用户输入
    request = Request(USER_INPUT, text)
    内层 while True:                   ← agent loop（阻塞用户输入）
        response = handler.process(request)
        FINISH   → render, break
        PROGRESS → render, request = CONTINUE（工具 handler 内可通过 UIBridge 直连 CLI 交互）
```

**模块分为两层：**

| 层 | 模块 | 说明 |
|----|------|------|
| 基础设施 | 配置模块 (`src/config.py`) | 启动时 `load_dotenv()` + 必填校验 → `SimpleNamespace` 单例；其他模块禁止 `os.environ` |
| 基础设施 | 日志模块 (`src/logger.py`) | `get_logger(__name__)` 懒加载；`RotatingFileHandler`（10MB×5）→ `data/logs/app.log`；stderr 输出 ERROR+ |
| 基础设施 | Message 模块 (`src/message.py`) | 数据总线：9 字段（event_type/id/role/timestamp/message/tool/tool_call_id/event_payload/thinking）；`Role(StrEnum)`（USER/SYSTEM/ASSISTANT）+ `EventType(StrEnum)` 双枚举 |
| 基础设施 | 提示词模块 (`src/prompts/`) | `PromptLoader.get()` 强制拼接 `general_agent/` → 替换 14 个占位符；`get_raw()` 跳过拼接 |
| 基础设施 | LLM 模块 (`src/llm/`) | `get_client()` 双检锁单例；双 tier（`chat_pro`/`chat_flash`）；`**kwargs` 透传；`_thinking_extra_body()` 控制 provider thinking |
| 基础设施 | RAG 模块 (`src/rag/`) | Chroma + `sentence_transformers`；`search()`/`load()`/`start()`/`is_ready()` 四个公开 API；bi-encoder 召回 → cross-encoder 重排 |
| 基础设施 | Tool 系统 (`src/tools/`) | `@tool` 装饰器注册 → `ToolRegistry` 全局管理；`input_schema` 扁平化，type/required 自动推断；`ToolCallException` 统一异常；handler 通过 `UIBridge`（`src/cli/uibridge.py`）直连 CLI 交互 |
| 基础设施 | UIBridge (`src/cli/uibridge.py`) | 跨线程通信桥：工具 handler（后台线程）调 `select()`/`confirm()` 阻塞等待，主线程 spinner 循环中轮询并渲染 questionary |
| 基础设施 | Lifecycle 模块 (`src/lifecycle.py`) | `register_shutdown(hook, name)` → `shutdown()` 逆序执行 |
| 基础设施 | CLI/App 层 (`src/cli/`) | `App`（I/O + 渲染 + 双循环）+ `Handler`（抽象协议）；`Request`/`Response` 为 App↔Agent 协议层，不进对话历史 |
| 基础设施 | 文件读取 (`src/utils/file_reader.py`) | `read_text(path, offset, limit)` / `list_directory(path)` / `search_text(root, pattern, ...)` / `read_pdf` / `read_docx`；charset-normalizer 编码检测 |
| 基础设施 | 状态管理 (`src/utils/saver.py`) | `SaveManager` 类：auto-save on FINISH → `data/save/{session_id}/`；`/restore` 恢复 `_history` + `_plan`；延迟 sub 清理防崩溃；`session.json` 持久化 plan 状态 |
| 基础设施 | 对话 dump (`src/utils/dumper.py`) | `dump_history(agent_name, history)` → `data/logs/<agent>_<datetime>_message.dump` |
| Agent | BaseAgent (`src/agents/base.py`) | 14 个抽象方法 + `process(Request) -> Response` 单步执行；`_pro_params`/`_flash_params` 默认 `response_format={"type": "json_object"}`；Plan 基础设施（`_plan` + 3 工具 + system_message 注入）；`dump_history()` 导出历史 |
| Agent | MainAgent (`src/agents/main_agent.py`) | 路由 Agent：只做意图识别 + 调度子 Agent，不执行领域任务 |
| Agent | ResumeAgent (`src/agents/resume/agent.py`) | 简历定制 Agent：workspace 工具直接操作 LaTeX 模板，`copy_template` → 填充占位符 → `build_pdf` → `workspace_open` |
| Agent | JobSearchAgent (`src/agents/job_search/agent.py`) | M4 测试用子 Agent |
| 服务 | 记忆模块 (`src/memory/`) | Facade：`build_memories`/`search_memories`/`delete_memory`；观察者模式（Store → 事件 → Indexer → RAG）解耦；按 Agent 分目录，一文件一条记忆 |

**记忆模块是唯一共享通道：** 所有 Agent 通过记忆模块读写上下文，记忆按 Agent 隔离存储在 `data/memories/<agent>/` 下。跨 Agent 检索通过 `search_memories(query, agent=None)` 走 RAG 语义搜索。

**Agent key 常量（`src/agents/registry.py`）：**
- `MAIN_AGENT_KEY = "main"`
- `RESUME_AGENT_KEY = "resume"`
- `JOB_SEARCH_AGENT_KEY = "job_search"`
- `INTERVIEW_AGENT_KEY = "interview"`

**工具模块清单：**

| 模块 | 工具 | 数量 |
|------|------|------|
| `system_tool.py` | `get_current_datetime`, `get_working_dir` | 2 |
| `web_tool.py` | `web_search` | 1 |
| `switch_tools.py` | `switch_to_subagent`, `switch_to_mainagent` | 2 |
| `plan_tools.py` | `create_plan`, `update_plan_status`, `cancel_all_plans` | 3 |
| `workspace_tools.py` | `workspace_read`, `workspace_list`, `workspace_grep`, `workspace_search_file`, `workspace_replace`, `workspace_write`, `workspace_delete`, `workspace_move`, `workspace_edit`, `workspace_open` | 10 |
| `customer_file_tool.py` | `read_customer_file` | 1 |
| `rag_tools.py` | `query_memory`, `query_reference_data` | 2 |
| `resume_tools.py` | `copy_template`, `build_pdf` | 2 |
| **总计** | | **23** |

详细设计见 `docs/design.md`。

## Key Conventions

- **不要写测试**，除非用户显式要求编写测试文件
- **同步代码**，不使用 `asyncio` 或任何异步框架
- **使用 `uv` 管理依赖和运行** — 运行项目 Python 代码必须带 `uv run` 前缀
- **`from src.config import config` 放在所有第三方 import 之前** — `config` import 触发 `load_dotenv()`，某些第三方库（`huggingface_hub`、`sentence_transformers`）在 import 时缓存 `os.environ`，必须先加载 `.env`
- **LLM 客户端用 `get_client()` 单例** — `from src.llm import get_client`，不要直接 `LLMClient()`；双检锁线程安全
- **提示词与代码分离** — 模板在 `data/prompts/`，`PromptLoader` 加载；Agent 调用 `get()` 自动拼接 `general_agent/`；非 Agent 模块用 `get_raw()`
- **LLM temperature 由 Agent `_pro_params` 控制** — 不在 LLMClient 层设默认值。MainAgent 0.1，ResumeAgent/JobSearchAgent 0.2，MemoryBuilder 0；调用方可通过 `**kwargs` 覆盖
- **Agent 必须实现 14 个抽象方法** — `_get_agent_name` + 13 个占位符方法（`_get_agent_description`、`_get_responsibilities` 等），遗漏 Python 在 import 时 `TypeError`
- **工具 handler 返回纯数据** — 返回 `str`/`dict`，由调用方（`BaseAgent._execute_tool()`）包装为 `tool_call_result` Message
- **`Request`/`Response` 是 App↔Agent 协议层** — 不进对话历史，与 `Message` 语义分离；`RequestType` 枚举（USER_INPUT/CONTINUE/CONFIRM_APPROVED），`ResponseType` 枚举（实际使用 FINISH/PROGRESS；CONFIRM/SELECT 已废弃）
- **工具审批由 `ConfirmMode` + UIBridge 共同控制** — `_execute_tool()` 根据 `ConfirmMode`（NEVER/ALWAYS/CONFIG）决定是否调 `get_bridge().confirm()` 弹审批窗；特殊交互（如 `provide_choices` 的 `select()`）由 handler 自行调用 UIBridge
- **Plan 机制为通用基础设施** — `BaseAgent` 层 3 个免审批工具（`create_plan`/`update_plan_status`/`cancel_all_plans`），`process()` 中通过 `_stamp_plan_status()` 将当前 plan 快照写入每条 `Message.plan_status`（不再拼接 system prompt）；MainAgent plan 全程存活，子 Agent plan 随 return 丢弃
- **工具访问 Agent 实例用 context variable** — 需访问 `self` 的工具（如 plan 工具）通过模块级 `_set_*()` / `_get_*()` 函数获取当前 Agent 实例，模式与 UIBridge（`_set_bridge`/`get_bridge`）一致
- **`EventType(StrEnum)` / `Role(StrEnum)` 双枚举** — 代码中禁止裸字符串；`EventType` 5 个值（USER_INPUT/TOOL_CALL/TOOL_CALL_RESULT/FINISH/SYSTEM_MESSAGE），`Role` 3 个值（USER/SYSTEM/ASSISTANT）
- **Cancel 中断机制** — 按 Esc 中断 agent loop：`_cancel_event`（`src/cli/uibridge.py`）跨线程取消信号；`_check_esc_pressed()`（`src/cli/app.py`）非阻塞检测；`process()` 中 3 个检查点；工具执行前取消时注入合成 `TOOL_CALL_RESULT`（`__cancelled__`）；cancel 标志在每次新请求开始时 `_clear_cancel()`。详见 `docs/design.md#417-agent-中断机制`
- **SYSTEM_MESSAGE role 分类** — 纠错类（output_format 注入、未知工具提示）→ `Role.SYSTEM`；正常上下文（plan 注入、退出提示）→ `Role.USER`
- **System prompt 不在 `_history` 中** — 单独 `_system_prompt` 字符串，`_to_openai()` 时以 `{"role": "system", "content": "..."}` 注入
- **`ToolCallException` 统一工具异常** — handler 抛 `ToolCallException(message, suggestion)`，框架层填充 `arguments_schema` + `expected_output` + `error_code`；handler 不感知 tool 定义
- **工具错误带上下文喂回 LLM 让其自修复** — 原则：给够上下文让 LLM 有能力自修复
- **Agent key 用常量引用** — `RESUME_AGENT_KEY` / `MAIN_AGENT_KEY` 等，不写裸字符串
- **StrEnum 用于 filter 枚举** — `MemoryType` / `ReferenceCategory` 保证 LLM 传入值与 metadata 约定一致，修改枚举时需同步更新对应文件（参见枚举 docstring）
- **设计/计划文件直接删除，不保留废弃内容** — Git 负责版本追溯
- **任务终止用 ⛔ 标记** — `docs/task.md` 中废弃任务标 ⛔ 并追加替代任务
- **暂缓任务用 📌 标记** — `docs/task.md` 中暂缓实现的任务标 📌
- **记忆固化时带分隔符** — Agent 写入记忆按 `---` 分隔，便于 Chunker 切分入库
- Agent 之间禁止直接调用，必须通过主 Agent 编排
- Agent 框架自研，不使用 LangChain/CrewAI/AutoGen 等现成框架
- LLM 对话压缩由 LLM 自身完成，不引入额外 NLP 依赖
- **Jupyter 调试** — `uv run --with jupyter --with jupyterlab-lsp --with jedi-language-server jupyter lab`，jupyter 不写入项目依赖
- **新模块先讨论设计** — 接口、职责边界、依赖关系确认后再动手
- **新文件先列方法清单** — 让用户确认后再创建
- **非交互模块测试后提供 Notebook 代码** — 让用户自行验证，不要仅给命令行结果
- **日志用 `get_logger(__name__)`** — 禁止 `print()`；失败记日志不抛异常（防御性编程）
- **禁止 Bash + Python 读写文件** — 必须用 Read/Edit/Write/Glob/Grep 专用工具
- **current.md 新增决策时同步更新 decision.md** — 编号体系保持一致
- **HF Hub 进度条在 RAG 模块 import 前静默** — `src/rag/__init__.py` 在 import `sentence_transformers` 前设置环境变量

## Doc Files

| 文件 | 用途 | 加载时机 |
|------|------|----------|
| `docs/current.md` | 当前状态快照（阶段/任务/阻塞/下一步） | 每次会话必读 |
| `docs/design.md` | 架构与模块设计（含 4.17 Agent 中断机制） | 涉及架构问题时 |
| `docs/plan.md` | 里程碑与实施计划 | 需要排期时或者当前任务下所有子任务都结束 |
| `docs/task.md` | 任务列表（阶段→任务→子任务，⬜🔄✅⏸️⛔📌） | 需要任务细节时 |
| `docs/decision.md` | 决策记录 | 需要历史决策理由时 |
