# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**get-me-in** — AI 求职助手，面向程序员的多 Agent 系统。CLI 交互，Python 3.14。

## Workflow

本项目遵循 **Plan → Execute → Result Validation → Replan** 循环。
工作完成后应使用 `/project-checkpoint` 更新 `docs/current.md` 和 `docs/task.md`。
新会话开始时使用 `/project-bootstrap` 恢复上下文。
**不要主动推进项目进度** — 完成当前任务后，主动提醒用户审查成果并保存状态（`/project-checkpoint`），由用户决定是否继续下一步。

## Architecture

**Hub-and-Spoke 模式：** 主 Agent 是唯一入口和调度中心。所有 Agent 共享相同的基础能力（对话循环、意图识别、工具调用、记忆读写），主 Agent 唯一特权是持有 `AgentRegistry` 调度子 Agent。子 Agent 之间不允许直接通信，也不允许持有或调度其他 Agent。

**模块分为两层：**

| 层 | 模块 | 说明 |
|----|------|------|
| 基础设施 | 提示词模块 (`src/prompts/`) | 加载 `data/prompts/` 下的模板；Agent 调用时强制拼接 `general_agent/` 公共前缀 |
| 基础设施 | RAG 模块 (`src/rag/`) | Chroma（内存模式）+ `sentence_transformers`；召回（bi-encoder）→ 重排（cross-encoder） |
| 基础设施 | 记忆模块 (`src/memory/`) | 按 Agent 分目录存储；持有 RAG 引用实现跨 Agent 语义检索 |
| 基础设施 | 日志模块 (`src/logger.py`) | 封装 `logging` 标准库；`RotatingFileHandler`（10MB × 5）→ `data/logs/app.log`；`StreamHandler(stderr)` 输出 ERROR+ |
| Agent | 主 Agent / 简历 / 学习 / 面试 / 岗位搜索 | 岗位搜索 Agent 为 TBD |

**记忆模块是唯一共享通道：** 所有 Agent 通过记忆模块读写上下文，记忆按 Agent 隔离存储在 `data/memories/<agent>/` 下。跨 Agent 检索通过 `MemoryStore.query_cross_agent()` 走 RAG 语义搜索。

详细设计见 `docs/design.md`。

## Key Conventions

- **不要写测试**，除非用户显式要求编写测试文件
- **同步代码**，不使用 `asyncio` 或任何异步框架
- **提示词与代码分离** — 提示词模板放在 `data/prompts/`，由 `src/prompts/loader.py` 加载；Agent 调用 `get()` 时自动在前面拼接 `general_agent/` 目录下所有文件；非 Agent 模块用 `get_raw()` 跳过拼接
- **设计/计划文件直接删除，不保留废弃内容** — `docs/design.md`、`docs/plan.md` 中不适用的内容直接删除，Git 负责版本追溯
- **任务终止用 ⛔ 标记** — `docs/task.md` 中废弃的任务标 ⛔ 并追加替代任务，不做删除
- **记忆固化时带分隔符** — Agent 写入记忆时按约定分隔符组织输出，便于 RAG 模块的 Chunker 切分入库
- Agent 实现 `src/agents/base.py` 定义的基类接口
- Agent 之间禁止直接调用，必须通过主 Agent 编排
- Agent 框架自研，不使用 LangChain/CrewAI/AutoGen 等现成框架
- LLM 对话压缩由 LLM 自身完成，不引入额外 NLP 依赖
- **使用 `uv` 管理依赖和运行** — 添加/移除依赖用 `uv add` / `uv remove`；运行项目内 Python 代码必须带 `uv run` 前缀（如 `uv run python main.py`）；安装依赖用 `uv sync`；构建发布用 `uv build`
- **`from src.config import config` 放在所有第三方 import 之前** — `config` 模块 import 时触发 `load_dotenv()` 注入环境变量。某些第三方库（如 `huggingface_hub`、`sentence_transformers`）在 import 时读取 `os.environ` 并缓存，必须先让 config 把 `.env` 加载完再导入它们
- **Jupyter 交互式调试** — 用 `uv run --with jupyter --with jupyterlab-lsp --with jedi-language-server jupyter lab` 启动 notebook 验证局部函数（含自动补全），`jupyter`/`jupyterlab-lsp`/`jedi-language-server` 均不写入项目依赖
- **新模块先讨论设计** — 每次开始实现新模块前，先与用户讨论模块设计细节（接口、职责边界、依赖关系），确认后再动手写代码。不要跳过讨论直接实现
- **新文件先列方法清单** — 每次准备新建代码文件之前，先告知用户该文件计划提供哪些功能/方法/类，让用户确认后再创建文件
- **非交互模块测试后提供 Notebook 代码** — 每次新模块测试完毕后，如果是非交互式功能（如 RAG 各组件），提供给用户一段可在 Jupyter Notebook 中运行的代码块，让用户自行验证；不要仅提供命令行测试结果
- **日志用 `get_logger(__name__)`** — 禁止 `print()` 调试；各模块通过 `from src.logger import get_logger` + `logger = get_logger(__name__)` 获取 logger；失败记日志不抛异常（防御性编程）
- **current.md 新增决策时同步更新 decision.md** — `docs/current.md` 的"重要决策"每新增一条编号，必须同步在 `docs/decision.md` 追加完整决策条目（背景/决策/理由/曾考虑的替代方案），两边的编号体系保持一致

## Doc Files

| 文件 | 用途 | 加载时机 |
|------|------|----------|
| `docs/current.md` | 当前状态快照（阶段/任务/阻塞/下一步） | 每次会话必读 |
| `docs/design.md` | 架构与模块设计 | 涉及架构问题时 |
| `docs/plan.md` | 里程碑与实施计划 | 需要排期时或者当前任务下所有子任务都结束 |
| `docs/task.md` | 任务列表（阶段→任务→子任务，⬜🔄✅⏸️⛔） | 需要任务细节时 |
| `docs/decision.md` | 决策记录 | 需要历史决策理由时 |
