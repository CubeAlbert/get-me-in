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

config = SimpleNamespace(**_values)
