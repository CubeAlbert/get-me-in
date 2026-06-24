# 任务列表

工作流遵循 **Plan → Execute → Result Validation → Replan** 循环。工作按三个层级组织：**阶段 → 任务 → 子任务**。阶段是顺序执行的 —— 完成一个阶段后再开始下一个。LLM 在创建时规划顺序，更新时必须保持该顺序。

| 符号 | 状态 | 含义 |
|------|------|------|
| ⬜ | 待开始 | 尚未开始 |
| 🔄 | 进行中 | 正在执行 |
| ✅ | 已完成 | 已完成 |
| ⏸️ | 阻塞 | 被阻塞 —— 在标记后注明原因 |
| ⛔ | 终止 | 任务被终止，由新任务替代 —— 在标记后注明替代原因，并在下方追加替代任务 |

状态标记设置在子任务上。任务和阶段的状态由子任务推导：若任一子任务为 🔄，其所属任务即为进行中；若所有子任务均为 ✅，则任务为已完成。

**终止规则：**
- 当某个任务不再适用或方向需要调整时，将当前未完成的子任务标记为 ⛔
- 在终止任务下方以 `>> 替代：[新任务名称]` 的格式追加替代任务
- 替代任务沿用子任务列表格式，从 ⬜ 开始
- 原终止任务保留在文档中，不做删除 —— 作为决策轨迹留存

---

> **后续阶段（M2-M8）尚未生成任务。** 当 M1 完成后，回到 `docs/design.md` 和 `docs/plan.md` 查看里程碑 2-8 的详细设计，再生成对应的 Task 列表。

## 阶段 1 —— M1: 项目骨架 & 基础设施

### 1. 项目配置 & 依赖

- ⬜ 完善 `pyproject.toml`：添加 `sentence_transformers`、`chromadb`、`rich`、LLM SDK（`openai` / `anthropic`）等依赖
- ⬜ 创建 `requirements.txt` 或使用 `pip install -e .` 验证依赖可安装

### 2. LLM 适配层 (`src/llm/`)

- ⬜ 实现 `client.py`：统一 LLM 调用接口（`chat(messages, **kwargs) -> str`）
- ⬜ 实现 `providers/` 下至少一个后端适配（Claude API 或 OpenAI）
- ⬜ 支持从环境变量读取 API Key

### 3. CLI 交互层 (`src/cli/`)

- ⬜ 实现 `app.py`：对话循环（`while True: input() → LLM → rich 渲染输出`）
- ⬜ 实现 `$EDITOR` 临时文件长文本输入（用户输入特殊命令时弹出编辑器）
- ⬜ `rich` 渲染 Markdown 输出（代码块、表格、列表等）

### 4. 提示词模块 (`src/prompts/`)

- ⬜ 实现 `loader.py`：扫描 `data/prompts/` 构建名称→模板映射；`get()` 替换变量；`get_raw()` 跳过公共前缀
- ⬜ 创建 `data/prompts/general_agent/safety.md`（安全策略）
- ⬜ 创建 `data/prompts/general_agent/tools.md`（可用工具列表）
- ⬜ 创建 `data/prompts/general_agent/output_format.md`（输出格式约定）
- ⬜ 创建 `data/prompts/orchestrator.md`（编排器意图识别提示词）
- ⬜ 创建 `data/prompts/memory_compressor.md`（对话压缩提示词）

### 5. 入口集成

- ⬜ 更新 `main.py`：初始化 LLM Client → PromptLoader → CLI App，串联完整对话流程
- ⬜ 端到端验证：启动程序 → 输入一句话 → LLM 返回 → rich 渲染输出
