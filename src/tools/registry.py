import inspect
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable, get_args, get_origin


_PY_TO_JSON_TYPE: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


class ConfirmMode(StrEnum):
    """工具审批模式，不暴露给 LLM。"""

    NEVER = "never"  # 无论全局开关，都不审批
    ALWAYS = "always"  # 无论全局开关，一律审批
    CONFIG = "config"  # 跟随全局 TOOL_CONFIRM_ENABLED


@dataclass
class Tool:
    """LLM 可调用的工具定义。

    由 ``@tool`` 装饰器自动构建并注册到 ``ToolRegistry``。
    ``to_xml()`` 渲染为 XML 块，注入 Agent 的 system prompt。
    """

    name: str
    purpose: str
    use_when: str
    do_not_use_when: str
    arguments_schema: str
    expected_output: str
    handler: Callable = field(repr=False)
    agent: list[str] | None = None
    confirm_mode: ConfirmMode = ConfirmMode.CONFIG

    def to_xml(self) -> str:
        """渲染为 ``04_tools.md`` 格式的 XML 块。"""
        return (
            f'<Tool name="{self.name}">\n'
            f"<Purpose>{self.purpose}</Purpose>\n"
            f"<UseWhen>{self.use_when}</UseWhen>\n"
            f"<DoNotUseWhen>{self.do_not_use_when}</DoNotUseWhen>\n"
            f"<Arguments>\n"
            f"{self.arguments_schema}\n"
            f"</Arguments>\n"
            f"<ExpectedOutput>{self.expected_output}</ExpectedOutput>\n"
            f"</Tool>"
        )


def _type_to_schema(py_type: type) -> str:
    """将 Python 类型转换为 LLM 可读的类型字符串。"""
    origin = get_origin(py_type)
    if origin is not None:
        # Union[X, None] → "X|null"
        args = get_args(py_type)
        if type(None) in args:
            inner = [a for a in args if a is not type(None)]
            base = _type_to_schema(inner[0]) if len(inner) == 1 else "object"
            return f"{base}|null"
        # Other generics: use origin mapping or fallback to "object"
        return _PY_TO_JSON_TYPE.get(origin, "object")

    return _PY_TO_JSON_TYPE.get(py_type, "object")


def _build_arguments_schema(
    fn: Callable,
    input_schema: dict[str, dict],
) -> str:
    """从函数签名自动补全 ``type`` / ``required``，生成 JSON schema 字符串。"""
    sig = inspect.signature(fn)
    completed: dict[str, dict] = {}

    for param_name, param_info in input_schema.items():
        entry: dict = {"description": param_info.get("description", "")}

        if param_name in sig.parameters:
            p = sig.parameters[param_name]
            entry["type"] = _type_to_schema(p.annotation) if p.annotation is not inspect.Parameter.empty else "string"
            entry["required"] = p.default is inspect.Parameter.empty
        else:
            entry["type"] = param_info.get("type", "string")
            entry["required"] = param_info.get("required", False)

        if "default" in param_info:
            entry["default"] = param_info["default"]

        completed[param_name] = entry

    return json.dumps(completed, ensure_ascii=False, indent=2)


def tool(
    *,
    purpose: str,
    use_when: str,
    do_not_use_when: str,
    expected_output: str,
    input_schema: dict[str, dict] | None = None,
    agent: list[str] | None = None,
    confirm_mode: ConfirmMode = ConfirmMode.CONFIG,
):
    """装饰器：将函数注册为 LLM 可调用工具。

    ``input_schema`` 只需写 ``description`` 和可选的 ``default`` ——
    装饰器通过 ``inspect.signature`` 自动从类型标注推断 ``type``、
    从默认值推断 ``required``。
    """
    input_schema = input_schema or {}

    def decorator(fn: Callable):
        schema = _build_arguments_schema(fn, input_schema)
        t = Tool(
            name=fn.__name__,
            purpose=purpose,
            use_when=use_when,
            do_not_use_when=do_not_use_when,
            arguments_schema=schema,
            expected_output=expected_output,
            handler=fn,
            agent=agent,
            confirm_mode=confirm_mode,
        )
        ToolRegistry.register(t)
        return fn

    return decorator


class ToolRegistry:
    """全局工具注册表。

    所有通过 ``@tool`` 装饰的工具自动注册到此。
    ``BaseAgent`` 通过 ``get_for()`` 按 agent 过滤拉取。
    """

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get_for(cls, agent_name: str, *, agent_key: str | None = None, main_key: str = "main") -> dict[str, Tool]:
        def _visible(tool: Tool) -> bool:
            if tool.agent is None:
                return True
            if "*" in tool.agent:
                return agent_key != main_key
            if agent_name in tool.agent:
                return True
            if agent_key is not None and agent_key in tool.agent:
                return True
            return False

        return {name: tool for name, tool in cls._tools.items() if _visible(tool)}

    @classmethod
    def list_all(cls) -> dict[str, Tool]:
        return dict(cls._tools)
