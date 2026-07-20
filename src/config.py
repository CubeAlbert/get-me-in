"""配置模块 — 集中管理所有环境变量。

应用启动时 import 本模块即完成 .env 加载和必填变量校验。
其他模块通过 `from src.config import config` 获取配置值，
禁止直接使用 `os.environ`。

用法:
    from src.config import config

    client = openai.OpenAI(
        base_url=config.OPENAI_BASE_URL,
        api_key=config.OPENAI_API_KEY,
    )

注意：在 _VAR_SPECS 中添加新变量时，必须同步更新项目根目录的
.env.example 文件（追加对应的注释和默认值）。
"""

import os
import sys
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv()

from src.logger import get_logger

logger = get_logger(__name__)
logger.debug(".env 文件已加载")

_VAR_SPECS: list[tuple[str, bool, str | None, bool]] = [
    ("OPENAI_BASE_URL",   True, None, False),
    ("OPENAI_API_KEY",    True,  None, False),
    ("LLM_PRO_MODEL",     True, None, False),
    ("LLM_FLASH_MODEL",   True, None, False),
    ("BI_ENCODER_MODEL",  False, "BAAI/bge-base-zh-v1.5", False),
    ("CROSS_ENCODER_MODEL", False, "BAAI/bge-reranker-v2-m3", False),
    ("EMBED_BATCH_SIZE",  False, "32", False),
    ("CHROMA_PERSIST_DIR",  False, None, False),
    ("RETRIEVAL_TOP_K",    False, "10", False),
    ("RERANK_BATCH_SIZE",  False, "32", False),
    ("RERANK_TOP_K",       False, "5", False),
    ("HF_ENDPOINT",        False, None, False),
    ("LOG_LEVEL",          False, "INFO", False),
    ("LOG_DIR",            False, "data/logs/", False),
    ("MEMORIES_BASE_DIR",  False, "data/memories/", False),
    ("SHOW_THINKING",      False, "false", True),
    ("AGENT_MAX_ROUNDS",       False, "10", False),
    ("TOOL_CONFIRM_ENABLED",   False, "true", True),
    ("WORKING_DIR",            False, "data/temp/", False),
    ("LLM_THINKING_ENABLED",  False, "true", True),
    ("SAVE_DIR",            False, "data/save/", False),
    ("AUTO_MEMORY_ON_EXIT",  False, "false", True),
]

_missing: list[str] = []
_values: dict = {}

for _name, _required, _default, _is_bool in _VAR_SPECS:
    _value = os.environ.get(_name)
    if _value is None and _default is not None:
        _value = _default
    if _value is None:
        if _required:
            _missing.append(_name)
    else:
        if _is_bool:
            _value = _value.lower() in ("true", "1")
        _values[_name] = _value

logger.debug("环境变量: %s", dict(sorted(_values.items())))

if _missing:
    logger.error("缺少 %d 个必填环境变量: %s", len(_missing), _missing)
    print("Missing required environment variables:")
    for _name in _missing:
        print(f"  • {_name}")
    print()
    print("Check your .env file or set them directly.")
    sys.exit(1)

# 将已解析的值回写 os.environ，确保第三方库（如 sentence_transformers、
# huggingface_hub）能读取到 HF_ENDPOINT 等配置（这些库不通过本模块获取配置，
# 而是直接读 os.environ）
for _name, _value in _values.items():
    os.environ.setdefault(_name, str(_value))

logger.debug("环境变量校验通过，共 %d 项", len(_values))

config = SimpleNamespace(**_values)
