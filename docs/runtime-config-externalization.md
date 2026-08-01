# 运行配置硬编码外置专项计划

## 1. 状态与授权门禁

- **当前状态：** 方案已整理，尚未实施。
- **实施会话：** 用户明确要求不在当前会话实施，留待新会话执行。
- **阶段边界：** 本专项是 R8 完成态后的独立配置治理，不进入 R9，不检查、设计或实施 InterviewAgent、Workflow、Job Search、LearningAgent 或 Sticky Plan。
- **数据边界：** 不读取、迁移、改写或删除 `data/save/`、`data/memories/`、`data/chroma/`、`data/temp/`；本地 `.env` 中的密钥和值不得写入日志、测试输出、diff 或文档。
- **停止规则：** 新会话开始前必须执行 `/project-bootstrap`，复核 `docs/current.md`、本文件和决策 274；若实际实现需要超出本文件白名单、新增 production module、依赖、公开协议或数据迁移，立即停止并提交最小扩展清单。

## 2. 目标

1. 把所有部署／运行时可调参数从生产代码字面量迁移到 `.env`／`.env.example`。
2. 保留当前默认行为，不借配置治理改变模型、Chroma 模式、Agent 能力、CLI 命令或数据位置。
3. 让 `.env.example` 成为唯一、完整的配置清单；生产代码不再保存第二套运行默认值。
4. 应用配置通过 typed `Settings` 统一解析、验证和显式注入；第三方库原生环境键是明确记录的唯一例外，业务模块不得直接读取环境变量。
5. 保留协议、持久化、安全和算法不变量在代码中，避免“全部外置”退化为任意配置可破坏系统契约。

## 3. 当前基线与已确认问题

- `.env` 已在前一会话按变量名与 `.env.example` 同步为 25 项；`.env` 被 Git 忽略，值不得进入仓库。
- `Settings.from_env()` 仍为多数现有变量保留代码默认值；即使 `.env.example` 漂移或缺项，生产可能静默使用代码中的第二套默认值。
- 以下路径仍直接在 `Settings.from_env()` 中拼接：reference、prompts、resume template、knowledge manifest、knowledge Chroma、memories。
- Main、Resume、Memory 的 model profile／temperature，模型格式修复上限，Web Search token 上限仍在 composition、AgentSpec、Runtime 或 adapter 中固定。
- 日志轮转、CLI／子进程轮询、CLI 预览长度、Session 预览长度和 Tool 默认分页仍由调用点字面量控制。
- 模型加载进度与第三方 logger 静默策略仍由 `cli/main.py` 的模块常量写入环境。

## 4. 配置与代码不变量的分界

### 4.1 必须外置

满足任一条件即视为运行配置：

- 部署环境可能需要更换的路径、模型或模型 profile；
- 性能、资源占用、超时、批量、token、重试／修复次数、日志轮转；
- CLI 展示截断、轮询周期和 Tool 的可选参数默认值；
- 第三方模型库的进度和日志显示设置。

### 4.2 必须保留在代码中

- Session／Artifact／Manifest schema version 与兼容读取规则；
- Agent key、Capability、Runtime 状态、Tool 名称、collection/category、Memory 类型；
- `json_object` 模型输出协议、Web Search function-call 协议和 DSML 未执行调用检测；
- Memory／Web Search 强制关闭 thinking 的专用调用契约；
- XeLaTeX、`-no-shell-escape`、UTF-8、`errors="replace"` 和原子写入安全边界；
- 敏感参数脱敏名单、路径授权、单 Worker、handoff 深度和 PENDING → effect → COMMITTED；
- 1-indexed 行号、队列容量、hash 读取缓冲区等不改变产品行为的实现细节。

这些内容不是部署选择，不得仅为消除字面量而环境变量化。

## 5. 新增配置清单与默认值

以下变量追加到 `.env.example`；本地 `.env` 同步添加，使用当前代码行为作为初始值。

### 5.1 静态输入与数据路径

```dotenv
REFERENCE_DIR=data/reference
PROMPTS_DIR=data/prompts
RESUME_TEMPLATE_DIR=data/resume/template
KNOWLEDGE_MANIFEST_PATH=data/v2/knowledge/manifest.json
KNOWLEDGE_CHROMA_DIR=data/v2/knowledge/chroma
MEMORIES_DIR=data/v2/memories
```

### 5.2 模型 profile 与运行策略

```dotenv
MAIN_MODEL_PROFILE=pro
RESUME_MODEL_PROFILE=pro
MEMORY_MODEL_PROFILE=flash
WEB_SEARCH_MODEL_PROFILE=pro
MAIN_TEMPERATURE=0.1
RESUME_TEMPERATURE=0.2
MEMORY_TEMPERATURE=0.0
MODEL_FORMAT_REPAIR_LIMIT=3
WEB_SEARCH_MAX_TOKENS=4096
```

`MODEL_FORMAT_REPAIR_LIMIT` 表示每个 Agent 用户 turn 允许安排的模型格式 repair 次数；默认 3，下一次格式错误暂停。它不改变本地 JSON repair 不计数、新 `UserMessage` 清零或 snapshot canonical 计数契约。

### 5.3 日志、轮询与 CLI 展示

```dotenv
LOG_FILE_NAME=app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
CLI_WORKER_POLL_INTERVAL_SECONDS=0.1
SUBPROCESS_POLL_INTERVAL_SECONDS=0.05
CLI_RESULT_PREVIEW_CHARS=500
CLI_ARGUMENT_PREVIEW_CHARS=160
SESSION_PREVIEW_CHARS=80
```

### 5.4 Tool 默认值

```dotenv
WORKSPACE_READ_DEFAULT_LIMIT=100
WORKSPACE_SEARCH_MAX_MATCHES=50
WORKSPACE_FILE_SEARCH_MAX_RESULTS=50
CUSTOMER_FILE_READ_DEFAULT_LIMIT=100
RETRIEVAL_DEFAULT_TOP_K=5
```

`RETRIEVAL_DEFAULT_TOP_K` 是 Tool 未显式传参时的查询数量；现有 `RETRIEVAL_TOP_K=8` 继续表示 reranker 输出上限，两者不得合并。

### 5.5 第三方模型加载显示

```dotenv
HF_HUB_DISABLE_PROGRESS_BARS=1
TQDM_DISABLE=1
TRANSFORMERS_VERBOSITY=error
MODEL_LIBRARY_LOG_LEVEL=ERROR
```

前三项由第三方库直接消费；`MODEL_LIBRARY_LOG_LEVEL` 由 CLI 用于 `huggingface_hub`、`transformers`、`sentence_transformers` logger。不得继续在代码中保存同值 `_MODEL_LOADING_ENV`。

## 6. Settings 契约

### 6.1 唯一默认值来源

- `.env.example` 保存可复制的当前默认值；`.env` 保存本地真实值。
- `Settings` 的运行配置字段不再声明行为默认值，`from_env()` 不再使用 `env.get(name, hardcoded_default)`。
- 所有应用配置键必须存在；缺失时返回 `SettingsValidationError` 并由根入口以退出码 2 结束。
- `HF_ENDPOINT` 的键必须存在但允许空值，空值投影为 `None`；API key、URL、模型名、profile、路径和文件名不得为空。
- shell／进程环境继续优先于 `.env`，保持 `load_dotenv(..., override=False)` 语义。
- `Settings.from_env()` 接收完整进程环境，因此不拒绝未知系统环境变量；`.env`／`.env.example` 的变量集合一致性由专门测试和同步检查保证。

### 6.2 类型与范围

- `*_MODEL_PROFILE`：只允许 `pro|flash`，解析为 `ModelProfile` 或等价 typed value。
- temperature：有限数且位于 `[0, 2]`。
- timeout、poll interval、token、byte、preview、Tool limit：严格大于 0。
- `MODEL_FORMAT_REPAIR_LIMIT`、`LOG_BACKUP_COUNT`：允许 0 的非负整数。
- bool：继续只接受 `true|false|1|0`。
- log level：继续只接受 `DEBUG|INFO|WARNING|ERROR|CRITICAL`。
- `LOG_FILE_NAME`：必须是单一普通文件名，不允许目录分隔符、`.`、`..` 或绝对路径。

### 6.3 路径与 legacy 拒绝

- 所有相对路径统一相对于 `project_root` 解析；显式绝对路径允许保留。
- 解析使用规范化绝对路径进行安全比较，但不得要求目标预先存在。
- `WORKSPACE_DIR`、`SESSIONS_DIR`、`ARTIFACTS_DIR`、`LOG_DIR`、新增六个路径中的任意一项，不得等于或位于以下项目内 legacy 根目录：
  - `data/save/`
  - `data/memories/`
  - `data/chroma/`
  - `data/temp/`
- memory mode 仍不得创建、读取或改写 `KNOWLEDGE_MANIFEST_PATH`／`KNOWLEDGE_CHROMA_DIR`；路径可配置不改变 mode 生命周期契约。

## 7. 显式注入映射

- `bootstrap.py`
  - Main AgentSpec 使用 `MAIN_MODEL_PROFILE`／`MAIN_TEMPERATURE`。
  - `build_resume_spec()` 接收 `RESUME_MODEL_PROFILE`／`RESUME_TEMPERATURE`。
  - MemoryExtractor 使用 `MEMORY_MODEL_PROFILE`／`MEMORY_TEMPERATURE`。
  - Web Search 由 `WEB_SEARCH_MODEL_PROFILE` 解析实际模型，并接收 `WEB_SEARCH_MAX_TOKENS`。
  - 两个 Runtime 都接收 `MODEL_FORMAT_REPAIR_LIMIT`。
  - Tool builder 接收对应默认值，schema 文案、`ToolParameter.default` 与 handler fallback 必须来自同一参数。
- `cli/main.py`
  - 先加载 `.env`、解析 Settings，再配置第三方 logger；移除 `_MODEL_LOADING_ENV` 写入。
  - Renderer、Logging、WorkerRunner 显式接收 Settings。
- `logging_setup.py`
  - `configure_logging()` 显式接收文件名、max bytes、backup count；所有“写入 app.log”用户提示改为使用真实日志文件名或返回路径。
- `runtime.py`
  - 移除 `_MAX_FORMAT_REPAIRS`，构造时接收非负 limit；错误消息使用实例值。
- `memory_extractor.py`
  - 构造时接收 typed model profile 与 temperature，不保留 `FLASH`／`0.0` 字面量。
- CLI／adapter／repository／tool
  - WorkerRunner、SubprocessRunner、Renderer、JsonSessionRepository、command choice preview 和三个 Tool builder 都由 composition 显式注入当前默认值。

除 `cli/main.py` composition root 将进程环境交给 `Settings.from_env()`、以及第三方库消费本计划列出的三个原生环境键外，不得让 adapter、tool handler 或其他 CLI 模块直接读取 `os.environ`。

## 8. 生产文件白名单

允许修改：

- `.env.example`
- 本地 `.env`（被 Git 忽略，只做无泄密同步）
- `src/get_me_in/application/settings.py`
- `src/get_me_in/bootstrap.py`
- `src/get_me_in/cli/main.py`
- `src/get_me_in/logging_setup.py`
- `src/get_me_in/application/runtime.py`
- `src/get_me_in/application/memory_extractor.py`
- `src/get_me_in/agents/resume.py`
- `src/get_me_in/adapters/openai_web_search.py`
- `src/get_me_in/adapters/subprocess_runner.py`
- `src/get_me_in/cli/worker.py`
- `src/get_me_in/cli/renderer.py`
- `src/get_me_in/cli/commands.py`
- `src/get_me_in/adapters/json_session_repository.py`
- `src/get_me_in/tools/workspace.py`
- `src/get_me_in/tools/customer_file.py`
- `src/get_me_in/tools/retrieval.py`

不新增 production module、依赖、CLI command、Settings loader、port、domain type、RuntimeEvent 或持久化字段。

## 9. 测试白名单与必需覆盖

允许按实际消费点修改以下测试；若需要其他测试文件，先证明直接相关并记录扩展原因：

- `tests/get_me_in/test_settings.py`
- `tests/get_me_in/test_bootstrap.py`
- `tests/get_me_in/test_cli_main.py`
- `tests/get_me_in/test_logging_setup.py`
- `tests/get_me_in/test_runtime.py`
- `tests/get_me_in/test_memory_service.py`
- `tests/get_me_in/test_resume_agent.py`
- `tests/get_me_in/test_web_tools.py`
- `tests/get_me_in/test_cli_worker.py`
- `tests/get_me_in/test_subprocess_runner.py`
- `tests/get_me_in/test_cli_commands.py`
- `tests/get_me_in/test_json_session_repository.py`
- `tests/get_me_in/test_workspace_tools.py`
- `tests/get_me_in/test_customer_file_tools.py`
- `tests/get_me_in/test_retrieval_tools.py`
- `tests/get_me_in/test_tool_catalog.py`

必需覆盖：

1. `.env.example` 包含完整 canonical key 集，且没有已删除 legacy alias。
2. 每个新增变量的成功解析、边界值与非法值。
3. 缺失任一应用配置键时 fail-fast；错误只列键名，不包含其他配置值。
4. 相对／绝对路径解析和四个 legacy 根目录及其子路径拒绝。
5. Main／Resume／Memory／Web Search profile 和 temperature／token 实际进入请求或构造参数。
6. format repair limit 0、1、3 的边界；默认 3 继续满足第四次错误暂停。
7. 日志文件名、轮转大小、备份数和用户提示一致。
8. CLI／子进程轮询值被 composition 消费。
9. Renderer／Session／rewind preview 使用同一配置且保持脱敏。
10. Tool schema 描述、default 与 handler fallback 一致；调用方显式参数仍优先。
11. `.env` 与 `.env.example` 只比较键和结构，不输出值；同步后使用真实 `.env` 构造 Settings 成功。

## 10. 实施切片与 checkpoint

### E0 —— 新会话恢复与基线

- 执行 `/project-bootstrap`，读取四份核心文档、本文件和决策 274。
- 确认分支 `refactor`、工作区干净、R9 未授权、计划 checkpoint 存在。
- 运行当前 Settings 定向测试和完整 unittest，记录基线；不得因本机 `uv` 默认 cache 拒绝访问而改项目配置，使用本次运行可写 cache 后重跑同一命令。

### E1 —— canonical Settings 与路径

- 先扩充 `.env.example`，无泄密同步 `.env`。
- 完成 Settings 字段、required key、typed parser、统一 path resolver 和 legacy refusal。
- 更新 Settings／CLI main 测试；运行定向测试、compileall、diff-check。
- 独立代码／测试 checkpoint；未通过不得进入 E2。

### E2 —— 模型、Runtime、日志与 adapter

- 注入 profile、temperature、repair limit、Web Search token、日志轮转、model logger 和两类 poll interval。
- 更新对应构造与测试，证明当前默认行为逐项不变。
- 独立代码／测试 checkpoint；未通过不得进入 E3。

### E3 —— CLI 预览与 Tool 默认值

- 注入 result／argument／session preview 与五个 Tool default。
- Tool schema 文案、default 和 handler 使用同一来源，不得形成三份值。
- 更新 ToolCatalog 快照／行为测试；独立代码／测试 checkpoint。

### E4 —— 完整门禁

依次运行：

```powershell
uv run python -m unittest discover -s tests/get_me_in -t .
uv run python -m compileall src/get_me_in main.py
git diff --check
```

并执行：

- 静态扫描：生产代码中不再出现本计划列出的旧硬编码值或直接环境读取；协议／安全不变量允许保留。
- 真实根入口配置 smoke：有效 `.env` 可启动并 `/exit`；缺失／非法新增配置返回 2，终端无 traceback。
- `.env`／`.env.example` key/shape 一致检查，任何输出只包含键名。
- persistent／memory composition component smoke：自定义新路径正确注入，memory 不触碰磁盘路径；不需要重新下载模型或重复真实 provider smoke。
- legacy refusal smoke：四个旧目录继续不可接入。

### E5 —— 文档收口

- 更新 `docs/design.md` 当前配置事实。
- 更新 `docs/task.md` 完成状态。
- 在 `docs/decision.md` 追加完成决策并同步 TOC。
- 更新 `docs/current.md`，保留最近 10 条摘要并继续关闭 R9 门禁。
- 文档独立 checkpoint；等待用户审查。

## 11. 验收标准

- `.env.example` 是唯一运行默认值清单；Settings、adapter、Runtime、CLI、Tool 不再保存本计划所列运行默认字面量。
- `.env` 与 `.env.example` 的键和结构一致，现有密钥及显式本地值保留且未泄露。
- 当前默认配置下行为与本专项前一致。
- 任一缺失／非法配置产生明确、非终止型 Settings 错误和根入口退出码 2。
- 新路径不能接入四个 legacy 数据目录，memory／persistent 生命周期不变。
- Tool schema、Prompt 可见 default 和 handler 实际 fallback 一致。
- 完整测试、compileall、diff-check、静态扫描和规定 smoke 全部通过。
- 无新增依赖、production module、业务能力、CLI command、持久化 schema 或 R9 实现。

## 12. 新会话首条执行提示

可在新会话直接使用：

> 执行 `/project-bootstrap`，按 `docs/current.md` 路由读取 `docs/runtime-config-externalization.md` 和决策 274。确认 `refactor` 分支与干净工作区后，从 E0 基线开始，严格按 E1～E5 分片实施并 checkpoint。不要进入 R9，不输出 `.env` 值；若需要超出白名单、新增 production module／依赖／公开协议或接入 legacy 数据目录，立即停止并提交最小扩展清单。
