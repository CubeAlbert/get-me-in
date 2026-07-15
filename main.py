"""get-me-in — AI 求职助手。"""

from src.config import config  # noqa: F401  import 即触发 .env 加载和校验
from src.agents.job_search import JobSearchAgent
from src.agents.main_agent import MainAgent
from src.agents.registry import JOB_SEARCH_AGENT_KEY, get_agent_registry
from src.llm import get_client
from src.logger import get_logger
from src.prompts.loader import PromptLoader
from src.cli.app import App
from src.rag import start
import src.tools.plan_tools    # noqa: F401 — 触发 @tool 注册（plan）
import src.tools.switch_tools  # noqa: F401 — 触发 @tool 注册（switch）
import src.tools.system_tool  # noqa: F401 — 触发 @tool 注册
import src.tools.web_tool        # noqa: F401 — 触发 @tool 注册
import src.tools.workspace_tools  # noqa: F401 — 触发 @tool 注册（workspace_*）

logger = get_logger(__name__)


def main() -> None:
    logger.info("启动 get-me-in...")
    start()  # 后台加载 RAG 模型+数据，不阻塞 CLI

    llm = get_client()
    logger.info("LLM 客户端初始化完成")

    prompts = PromptLoader()
    logger.info("提示词加载器初始化完成")

    # 注册子 Agent（必须在 MainAgent 实例化前，使其进入 system prompt）
    registry = get_agent_registry()
    registry.register(JOB_SEARCH_AGENT_KEY, JobSearchAgent(llm, prompts))
    logger.info("JobSearchAgent 已注册")

    handler = MainAgent(llm, prompts)
    logger.info("MainAgent 初始化完成")

    app = App(handler=handler)
    logger.info("进入主循环")
    app.run()

    from src.lifecycle import shutdown
    shutdown()
    logger.info("get-me-in 退出")


if __name__ == "__main__":
    main()
