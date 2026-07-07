"""get-me-in — AI 求职助手。"""

from src.config import config  # noqa: F401  import 即触发 .env 加载和校验
from src.agents.main_agent import MainAgent
from src.llm.client import LLMClient
from src.logger import get_logger
from src.prompts.loader import PromptLoader
from src.cli.app import App
from src.rag import start
import src.tools.system_tool  # noqa: F401 — 触发 @tool 注册

logger = get_logger(__name__)


def main() -> None:
    logger.info("启动 get-me-in...")
    start()  # 后台加载 RAG 模型+数据，不阻塞 CLI

    llm = LLMClient()
    logger.info("LLM 客户端初始化完成")

    prompts = PromptLoader()
    logger.info("提示词加载器初始化完成")

    handler = MainAgent(llm, prompts)
    logger.info("MainAgent 初始化完成")

    app = App(handler=handler)
    logger.info("进入主循环")
    app.run()


if __name__ == "__main__":
    main()
