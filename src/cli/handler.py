"""Handler 协议 — CLI 层与业务逻辑层之间的桥接接口。

CLI 不直接调用 LLM 或 Agent，而是调用注入的 Handler。
Handler 负责具体的输入处理逻辑，CLI 只负责 I/O 和渲染。

M1 阶段用 DemoHandler 桩验证 I/O 管线；
后续主 Agent 实现同一 process() 接口后无缝替换。
"""

from abc import ABC, abstractmethod


class Handler(ABC):
    """处理用户输入的抽象协议。

    所有业务逻辑入口（Agent、编排器等）均实现此接口，
    CLI 层只依赖 Handler，不感知具体实现。
    """

    @abstractmethod
    def process(self, user_input: str) -> str:
        """处理用户输入，返回响应文本（markdown 格式）。

        Args:
            user_input: 用户原始输入

        Returns:
            markdown 格式的响应文本，由 CLI 层用 rich 渲染
        """
        ...


class DemoHandler(Handler):
    """桩实现 — 用于测试 CLI I/O 管线。

    输入 1 → 纯文本
    输入 2 → markdown（代码块、表格、列表）
    输入 3 → 选项列表
    """

    def process(self, user_input: str) -> str:
        key = user_input.strip()

        if key == "1":
            return "Hello! 👋 这是一段**纯文本**回复。"

        if key == "2":
            return """\
# Markdown 渲染测试

## 代码块

```python
def hello():
    print("Hello, get-me-in!")
```

## 表格

| 模块 | 状态 | 说明 |
|------|------|------|
| 配置模块 | ✅ 完成 | 环境变量集中管理 |
| LLM 适配层 | ✅ 完成 | 双 tier 调用封装 |
| CLI 交互层 | 🔄 进行中 | 对话循环 + rich 渲染 |
| 提示词模块 | ⬜ 待开始 | PromptLoader |

## 无序列表

- 基础设施层：config / llm / cli / prompts
- RAG 层：embedder / chunker / store / retriever / reranker
- Agent 层：base / orchestrator / router

## 有序列表

1. 第一阶段：项目骨架 & 基础设施
2. 第二阶段：RAG 模块
3. 第三阶段：记忆模块
4. 第四阶段：Agent 基类 & 主 Agent
"""

        if key == "3":
            return """\
请选择一个操作：

- **1. 简历优化** — 上传简历，根据目标岗位定制优化
- **2. 技能学习** — 分析技能差距，生成学习路线
- **3. 模拟面试** — 选择岗位和难度，开始模拟面试
- **4. 岗位搜索** — 搜索匹配的职位并分析匹配度

输入数字选择，或输入 `/quit` 退出。
"""

        return f"未知输入: **{key}**。请输入 1、2 或 3。"
