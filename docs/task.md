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

- ✅ 完善 `pyproject.toml`：添加 `sentence_transformers`、`chromadb`、`rich`、`openai`、`python-dotenv` 等依赖
- ✅ `uv sync` 安装所有依赖并验证

### 2. 配置模块 (`src/config.py`)

- ✅ 实现 `config.py`：启动时调用 `load_dotenv()`、校验 4 个必填环境变量（缺失则打印清单并 `sys.exit(1)`）、将变量挂到模块属性上
- ⬜ 其他模块（LLM 等）统一 `from src.config import config` 获取配置，不再直接调用 `os.environ`

### 3. LLM 适配层 (`src/llm/`)

- ✅ 实现 `client.py`：`LLMClient` 双 tier 调用（`chat_pro()` / `chat_flash()`），从环境变量读取 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL`
- ✅ 创建 `.env.example` 模板文件（含 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_PRO_MODEL`、`LLM_FLASH_MODEL` 四项）

### 4. CLI 交互层 (`src/cli/`)

- ✅ 实现 `handler.py`：抽象基类 `Handler`（`process(user_input: str) -> str`）+ `DemoHandler`（输入 1→纯文本、2→markdown、3→选项列表），仅用于测试 I/O 管线
- ✅ 实现 `app.py`：`App` 类，依赖注入 `Handler`，对话循环 `while True: input() → handler.process() → rich`，不直接调 LLM
- ✅ 实现 `$EDITOR` 临时文件长文本输入（用户输入特殊命令时弹出编辑器）
- ✅ `rich` 渲染 Markdown 输出（代码块、表格、列表等）

### 5. 提示词模块 (`src/prompts/`)

- ✅ 实现 `loader.py`：`get(**kwargs)` 读取 `general_agent/` 下所有 `.md`（按文件名排序拼接）并替换占位符；`get_raw(name, **kwargs)` 加载 `data/prompts/<name>.md` 跳过拼接
- ✅ 创建 `data/prompts/general_agent/` 下 7 个模板文件（`01_role.md` ~ `07_reserved.md`）
- ✅ 创建 `data/prompts/PLACEHOLDER.md`（14 个 per-Agent 占位符清单）
- ⬜ 创建 `data/prompts/memory_compressor.md`（对话压缩提示词）—— ⚠️ 当前为空文件，待记忆模块（里程碑 3）实现时填充
- 编排不再使用独立提示词 —— 调度子 Agent 定义为工具，通过 `{{ADDITION_TOOLS}}` 注入

### 6. 入口集成

- ⬜ 更新 `main.py`：初始化 LLM Client → PromptLoader → CLI App，串联完整对话流程
- ⬜ 端到端验证：启动程序 → 输入一句话 → LLM 返回 → rich 渲染输出
