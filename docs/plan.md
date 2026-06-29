<!--
阅读指南：本文件可能较长。请先阅读目录，然后跳转到相关章节。
每次读取 100 行，直到该章节读完。
-->

# 实施计划

工作流遵循 **Plan → Execute → Result Validation → Replan** 循环。计划是动态的 —— 执行结果验证后可能推翻原有计划，此时直接删除不适用的内容并写入新计划。历史版本由 Git 负责，本文档始终只保留当前有效的计划。

## 目录

- [1. 里程碑](#1-里程碑)
- [2. 关键依赖](#2-关键依赖)

---

## 1. 里程碑

### 里程碑 1 —— 项目骨架 & 基础设施 ✅ 已完成

- **预期产出：** 可运行的项目骨架，LLM 能调用，CLI 能对话
- **验收标准：**
  - `pyproject.toml` 包含所需依赖
  - `src/config.py` 完成环境变量集中管理（启动加载 .env + 校验必填变量）
  - `src/llm/` 完成适配层封装，至少支持一个后端（Claude API 或 OpenAI）
  - `src/cli/app.py` 实现基本对话循环（`input()` + `rich` 渲染 Markdown 输出 + `$EDITOR` 长文本输入）
  - `src/prompts/loader.py` 完成：`get(**kwargs)` 拼接 `general_agent/` + 替换占位符；`get_raw(name, **kwargs)` 加载指定文件跳过拼接
  - `data/prompts/` 下 `general_agent/` 已创建 7 个模板文件（`01_role.md` ~ `07_reserved.md`），`memory_compressor.md` 已创建占位文件
  - `main.py` 能启动并完成一轮对话
- **前置依赖：** 无

### 里程碑 2 —— RAG 模块 ✅ 已完成

- **预期产出：** 可用的语义检索能力，支持写入和查询
- **验收标准：**
  - `src/rag/embedder.py` ✅ — 封装 `sentence_transformers` bi-encoder（`BAAI/bge-base-zh-v1.5`），模型名由环境变量配置
  - `src/rag/chunker.py` ✅ — 按 `---` 切分文本为逻辑块，附加 metadata，过滤空白片段
  - `src/rag/store.py` ✅ — 封装 Chroma（内存/持久化），内部持有 Embedder；`add()` / `query(query_text)` / `remove(source_file)`
  - `src/rag/loader.py` ✅ — 遍历 `data/reference/` + `data/memories/`，状态机（IDLE/LOADING/READY/ERROR），`auto_load()` daemon 后台加载，持久化模式 `.last_update` 增量，`reload(target)` 手动重载
  - `src/rag/reranker.py` ✅ — CrossEncoder 精排，分数注入 `metadata["rerank_score"]`，`__init__` 预热
  - `src/rag/__init__.py` ✅ — 公共入口：`search()` / `load()` / `is_ready()` 三个函数，内部双检锁懒加载单例
  - 端到端验证通过 ✅ — `search("快速排序")` 经召回→重排返回正确结果

### 里程碑 3 —— 记忆模块

- **预期产出：** 完整的记忆读写、压缩、跨 Agent 检索能力
- **验收标准：**
  - `src/memory/schemas.py` 定义 Profile、Preferences、Memory 数据结构
  - `src/memory/store.py` 实现文件系统读写：`get_profile()`、`get_preferences()`、`write_memory()`、`get_recent_memories()`、`query_cross_agent()`
  - `src/memory/compressor.py` 实现 LLM 对话压缩，输入对话消息列表，输出 Memory 列表
  - Memory ↔ RAG 接口：写入记忆时自动切分入库；跨 Agent 检索走 RAG 召回+重排
  - `data/memories/<agent>/` 目录结构就绪
- **前置依赖：** 里程碑 1（LLM）+ 里程碑 2（RAG）

### 里程碑 4 —— BaseAgent & 主 Agent

- **预期产出：** Agent 基类和可调度子 Agent 的主 Agent
- **验收标准：**
  - `src/agents/base.py` 定义 Agent 基类：对话循环、意图识别、工具调用、记忆读写便利方法（`self.write_memory()`、`self.get_recent_memories()`、`self.query_cross_agent()`）
  - `src/main_agent/orchestrator.py` 实现主循环和 Agent 调度（`AgentRegistry`）
  - `src/main_agent/router.py` 实现意图分类
  - 主 Agent 能根据用户意图路由到对应的子 Agent（初期子 Agent 可为桩实现）
  - `general_agent_prompt` 强制拼接生效
- **前置依赖：** 里程碑 1（提示词）+ 里程碑 3（记忆）

### 里程碑 5 —— 简历 Agent

- **预期产出：** 可用的简历分析和定制功能
- **验收标准：**
  - 解析用户简历（Markdown 输入），提取结构化信息
  - 根据 JD 定制简历，输出优化建议和修改后的简历
  - 分析结果和定制后的简历写入记忆模块
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 6 —— 学习 Agent

- **预期产出：** 技能差距分析和学习计划生成
- **验收标准：**
  - 读取用户档案和岗位要求，评估技能差距
  - 生成结构化学习计划并写入记忆模块
  - 支持进度查询和更新
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 7 —— 面试 Agent

- **预期产出：** 交互式模拟面试
- **验收标准：**
  - 根据岗位和技能生成针对性面试题
  - 支持交互式面试会话（开始→回答→反馈→结束）
  - 面试结束后生成报告并写入记忆模块
- **前置依赖：** 里程碑 4（BaseAgent）

### 里程碑 8 —— 岗位搜索 Agent

- **预期产出：** （待定 —— 方案确定后细化）
- **验收标准：** [待明确]
- **前置依赖：** 里程碑 4（BaseAgent）

## 2. 关键依赖

### 外部依赖

- `sentence_transformers` 模型下载 —— 首次加载需联网下载 bi-encoder 和 cross-encoder 模型文件
- LLM API（Claude API / OpenAI）—— 需要有效的 API Key 和网络访问

### 跨领域依赖

- BaseAgent（里程碑 4）是后续所有子 Agent 的前置条件 —— 简历/学习/面试三个 Agent 可并行开发，但均依赖 BaseAgent 就绪
- RAG 模块（里程碑 2）虽独立开发，但记忆模块（里程碑 3）强依赖它 —— RAG 的接口必须在里程碑 2 完成后稳定
- 提示词模块（里程碑 1）需在 Agent 开发前就绪 —— 所有 Agent 的 LLM 调用都走 PromptLoader

---

## 计划更新规则

- **直接删除：** 不适用的里程碑、验收标准或依赖项直接删除，不保留划掉或标记
- **直接追加：** 新里程碑追加到已有里程碑之后
- **版本控制：** 所有删除和修改的历史由 Git 追溯，本文档不保留废弃内容
