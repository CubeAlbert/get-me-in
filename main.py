"""get-me-in — AI 求职助手。"""

from src.config import config  # noqa: F401  import 即触发 .env 加载和校验
from src.llm.client import LLMClient
from src.prompts.loader import PromptLoader
from src.cli.app import App
from src.cli.handler import LLMHandler


def main() -> None:
    llm = LLMClient()
    prompts = PromptLoader()
    handler = LLMHandler(llm, prompts)
    app = App(handler=handler)
    app.run()


if __name__ == "__main__":
    main()
