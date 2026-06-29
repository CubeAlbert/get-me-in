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
"""

import os
import sys
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv()

_VAR_SPECS: list[tuple[str, bool, str | None]] = [
    ("OPENAI_BASE_URL",   True, None),
    ("OPENAI_API_KEY",    True,  None),
    ("LLM_PRO_MODEL",     True, None),
    ("LLM_FLASH_MODEL",   True, None),
    ("BI_ENCODER_MODEL",  False, "BAAI/bge-base-zh-v1.5"),
    ("CROSS_ENCODER_MODEL", False, "BAAI/bge-reranker-v2-m3"),
    ("EMBED_BATCH_SIZE",  False, "32"),
    ("CHROMA_PERSIST_DIR",  False, None),
    ("RETRIEVAL_TOP_K",    False, "10"),
    ("RERANK_BATCH_SIZE",  False, "32"),
    ("RERANK_TOP_K",       False, "5"),
    ("HF_ENDPOINT",        False, None),
]

_missing: list[str] = []
_values: dict[str, str] = {}

for _name, _required, _default in _VAR_SPECS:
    _value = os.environ.get(_name)
    if _value is None and _default is not None:
        _value = _default
    if _value is None:
        if _required:
            _missing.append(_name)
    else:
        _values[_name] = _value

if _missing:
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
    os.environ.setdefault(_name, _value)

config = SimpleNamespace(**_values)
