"""系统内置工具。"""

from datetime import datetime

from src.tools.registry import ConfirmMode, tool


@tool(
    purpose="获取当前的日期和时间（含时区），相信该工具的输出是准确的。",
    use_when="需要知道当前时间时",
    do_not_use_when="",
    expected_output="YYYY-MM-DD HH:mm:ss ±HHMM 格式的带时区日期时间字符串",
    confirm_mode=ConfirmMode.ALWAYS,
)
def get_current_datetime() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
