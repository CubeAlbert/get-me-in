"""系统内置工具。"""

from datetime import datetime
from pathlib import Path

from src.config import config
from src.tools.registry import ConfirmMode, tool


@tool(
    purpose="获取当前的日期和时间（含时区），相信该工具的输出是准确的。",
    use_when="需要知道当前时间时",
    do_not_use_when="",
    expected_output="YYYY-MM-DD HH:mm:ss ±HHMM 格式的带时区日期时间字符串",
    confirm_mode=ConfirmMode.NEVER,
)
def get_current_datetime() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


@tool(
    purpose="获取工作目录的绝对路径，该目录用于存放临时文件和输出文件。",
    use_when="需要在磁盘上读写文件时，文件路径都应以此目录为根目录。",
    do_not_use_when="",
    expected_output="工作目录的绝对路径字符串",
    confirm_mode=ConfirmMode.NEVER,
)
def get_working_dir() -> str:
    path = Path(config.WORKING_DIR).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
