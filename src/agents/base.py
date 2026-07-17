"""BaseAgent — Agent 基类，所有 Agent 的公共能力。

子类必须实现 14 个 ``_get_*`` 抽象方法（13 个占位符 + 1 个 agent_name），
遗漏任何一个 Python 会在 import 时报 ``TypeError``，防止漏填提示词。
"""

import inspect
import json
import uuid

from abc import abstractmethod

from src.agents.plan import PlanItem, PlanStatus
from src.cli.handler import Handler
from src.agents.registry import MAIN_AGENT_KEY
from src.tools.exceptions import ToolCallException
from src.cli.uibridge import get_bridge
from src.config import config
from src.llm.client import LLMClient
from src.logger import get_logger
from src.message import EventType, Message, Role
from src.prompts.loader import PromptLoader
from src.request import Request, RequestType
from src.response import Response, ResponseType
from src.tools.registry import ConfirmMode, Tool, ToolRegistry

logger = get_logger(__name__)


class BaseAgent(Handler):
    """Agent 基类 — 提供 agent loop、工具调度、对话管理、记忆写入。

    子类按需覆盖 ``_pro_params`` / ``_flash_params``（LLM 参数默认值）。
    """

    _pro_params: dict = {"response_format": {"type": "json_object"}}
    _flash_params: dict = {"response_format": {"type": "json_object"}}

    # ── 14 个抽象方法：子类必须全部实现 ──────────────────────

    @abstractmethod
    def _get_agent_name(self) -> str:
        """Agent 展示名 → ``{{AGENT_NAME}}``，用于 prompt 和记忆归属。"""
        ...

    def _get_agent_key(self) -> str:
        """Agent 稳定标识 → 用于工具过滤（``ToolRegistry.get_for``）。

        默认同 ``_get_agent_name()``，MainAgent 覆盖为 ``"main"``。
        """
        return self._get_agent_name()

    @abstractmethod
    def _get_agent_description(self) -> str:
        """→ AGENT_DESCRIPTION"""
        ...

    @abstractmethod
    def _get_responsibilities(self) -> str:
        """→ RESPONSIBILITIES"""
        ...

    @abstractmethod
    def _get_primary_goal(self) -> str:
        """→ PRIMARY_GOAL"""
        ...

    @abstractmethod
    def _get_success_criterions(self) -> str:
        """→ SUCCESS_CRITERIONS"""
        ...

    @abstractmethod
    def _get_priorities(self) -> str:
        """→ PRIORITIES"""
        ...

    @abstractmethod
    def _get_hard_constraints(self) -> str:
        """→ HARD_CONSTRAINTS"""
        ...

    @abstractmethod
    def _get_soft_constraints(self) -> str:
        """→ SOFT_CONSTRAINTS"""
        ...

    @abstractmethod
    def _get_tone(self) -> str:
        """→ TONE"""
        ...

    @abstractmethod
    def _get_verbosity(self) -> str:
        """→ VERBOSITY"""
        ...

    @abstractmethod
    def _get_explanation_style(self) -> str:
        """→ EXPLANATION_STYLE"""
        ...

    @abstractmethod
    def _get_style_rules(self) -> str:
        """→ STYLE_RULES"""
        ...

    @abstractmethod
    def _get_style_avoids(self) -> str:
        """→ STYLE_AVOIDS"""
        ...

    def _get_sub_agents_list(self) -> str:
        """→ SUB_AGENTS_LIST（默认空，MainAgent 覆盖）。"""
        return ""

    # ── init ──────────────────────────────────────────────

    def __init__(
        self,
        llm: LLMClient,
        prompts: PromptLoader,
        extra_tools: list[Tool] | None = None,
    ) -> None:
        name = self._get_agent_name()

        # 从 ToolRegistry 按 agent 过滤拉取工具
        self._tools = ToolRegistry.get_for(name, agent_key=self._get_agent_key(), main_key=MAIN_AGENT_KEY)
        if extra_tools:
            for t in extra_tools:
                self._tools[t.name] = t

        # 组装所有占位符值
        tools_xml = "\n".join(t.to_xml() for t in self._tools.values())
        placeholders = {
            "AGENT_NAME": name,
            "AGENT_DESCRIPTION": self._get_agent_description(),
            "RESPONSIBILITIES": self._get_responsibilities(),
            "PRIMARY_GOAL": self._get_primary_goal(),
            "SUCCESS_CRITERIONS": self._get_success_criterions(),
            "PRIORITIES": self._get_priorities(),
            "HARD_CONSTRAINTS": self._get_hard_constraints(),
            "SOFT_CONSTRAINTS": self._get_soft_constraints(),
            "ADDITION_TOOLS": tools_xml,
            "SUB_AGENTS_LIST": self._get_sub_agents_list(),
            "TONE": self._get_tone(),
            "VERBOSITY": self._get_verbosity(),
            "EXPLANATION_STYLE": self._get_explanation_style(),
            "STYLE_RULES": self._get_style_rules(),
            "STYLE_AVOIDS": self._get_style_avoids(),
        }
        system_prompt = prompts.get(**placeholders)

        self._llm = llm
        self._output_format = prompts.get_raw("general_agent/07_output_format")
        self._system_prompt = system_prompt
        self._history: list[Message] = []
        self._max_rounds = int(config.AGENT_MAX_ROUNDS)
        self._pending_tool: tuple[str, dict, str] | None = None
        self._pending_switch: tuple[str, str, str] | None = None
        self._pending_reject: bool = False
        self._round_counter = 0
        self._format_injected = False
        self._plan: list[PlanItem] = []

        logger.debug(
            "%s 初始化 — %d 个工具, max_rounds=%d",
            name,
            len(self._tools),
            self._max_rounds,
        )

    # ── debug ───────────────────────────────────────────────

    def debug_system_prompt(self) -> str:
        """返回完整系统提示词（含已注入的工具列表），供调试使用。"""
        return self._system_prompt

    # ── Plan 机制 ────────────────────────────────────────────

    def _get_active_plan(self) -> PlanItem | None:
        """返回当前 IN_PROGRESS 的计划项，无则返回 None。"""
        for item in self._plan:
            if item.status == PlanStatus.IN_PROGRESS:
                return item
        return None

    def _get_next_pending(self) -> PlanItem | None:
        """返回下一个 PENDING 项（按 order 排序），无则返回 None。"""
        pending = [i for i in self._plan if i.status == PlanStatus.PENDING]
        if not pending:
            return None
        return min(pending, key=lambda x: x.order)

    def _activate_next(self) -> None:
        """将下一个 PENDING 项设为 IN_PROGRESS。"""
        next_item = self._get_next_pending()
        if next_item:
            next_item.status = PlanStatus.IN_PROGRESS

    def _plan_summary(self) -> dict:
        """构建当前 plan 的摘要，作为 tool_call_result 返回给 LLM。"""
        items_data = [
            {
                "id": item.id,
                "description": item.description,
                "status": item.status.value,
                "order": item.order,
            }
            for item in self._plan
        ]
        active = self._get_active_plan()
        next_item = self._get_next_pending()
        all_done = (
            all(i.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED) for i in self._plan)
            if self._plan
            else True
        )
        return {
            "plan": items_data,
            "current": {"id": active.id, "description": active.description} if active else None,
            "next": {"id": next_item.id, "description": next_item.description} if next_item else None,
            "all_completed": all_done,
        }

    def _create_plan(self, items: list[str]) -> dict:
        """创建新计划（覆盖旧计划），首项自动激活为 IN_PROGRESS。"""
        self._plan = [
            PlanItem(
                id=uuid.uuid4().hex,
                description=desc,
                status=PlanStatus.PENDING,
                order=i,
            )
            for i, desc in enumerate(items)
        ]
        if self._plan:
            self._plan[0].status = PlanStatus.IN_PROGRESS
        return self._plan_summary()

    def _replan(self, items: list[str]) -> dict:
        """修订剩余计划：保留已完成项，替换未完成项。"""
        kept = [i for i in self._plan if i.status == PlanStatus.COMPLETED]
        new = [
            PlanItem(
                id=uuid.uuid4().hex,
                description=desc,
                status=PlanStatus.PENDING,
                order=len(kept) + i,
            )
            for i, desc in enumerate(items)
        ]
        if new:
            new[0].status = PlanStatus.IN_PROGRESS
        self._plan = kept + new
        return self._plan_summary()

    def _update_plan_status(self, plan_id: str, status: str) -> dict:
        """更新指定计划项的状态。完成/取消当前项时自动激活下一项。"""
        try:
            new_status = PlanStatus(status)
        except ValueError:
            return {"error": f"无效状态: {status}，可选: {[s.value for s in PlanStatus]}"}

        target = None
        for item in self._plan:
            if item.id == plan_id:
                target = item
                break

        if target is None:
            return {"error": f"未找到计划项: {plan_id}"}

        was_active = target.status == PlanStatus.IN_PROGRESS
        target.status = new_status

        if was_active and new_status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED):
            self._activate_next()

        return self._plan_summary()

    def _cancel_all_plans(self) -> dict:
        """取消所有未完成的计划项。"""
        for item in self._plan:
            if item.status not in (PlanStatus.COMPLETED, PlanStatus.CANCELLED):
                item.status = PlanStatus.CANCELLED
        return self._plan_summary()

    # ── process — agent loop ──────────────────────────────

    def _stamp_plan_status(self, msg: Message) -> None:
        """将当前 plan 简化摘要写入 Message.plan_status。"""
        from src.agents.plan import plan_to_simple
        msg.plan_status = plan_to_simple(self._plan)

    def _to_openai(self) -> list[dict]:
        """将 ``_history`` 转换为 OpenAI API 格式。

        system prompt 为纯文本，末尾附带 plan_status JSON（如有），对话消息序列化为 Message JSON。
        """
        messages = [{"role": "system", "content": self._system_prompt}]
        for m in self._history:
            messages.append({"role": m.role, "content": m.to_json()})
        return messages

    def dump_history(self) -> str | None:
        """将当前对话历史 dump 到日志目录，用于调试上下文丢失问题。

        Returns:
            dump 文件路径，失败返回 None。
        """
        from src.utils.dumper import dump_history

        return dump_history(self._get_agent_name(), self._history)

    def _execute_tool(self, tool_name: str, payload: dict, tool_call_id: str) -> Message | None:
        """执行工具并返回 tool_call_result Message。

        异常时附带工具定义（arguments_schema + expected_output），
        让 LLM 有足够上下文自修复调用参数。

        若 handler 返回 ``__switch__`` 标记，设 ``_pending_switch`` 并返回 None，
        调用方应跳过 tool_call_result 追加并处理切换。
        """
        tool = self._tools[tool_name]

        # 审批门禁：ConfirmMode 控制是否需要用户确认
        if self._should_confirm(tool):
            ui = get_bridge()
            params_str = json.dumps(payload, ensure_ascii=False)
            if not ui.confirm(f"即将执行 {tool_name}\n参数: {params_str}"):
                self._pending_reject = True
                return Message(
                    role=Role.USER,
                    event_type=EventType.TOOL_CALL_RESULT,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    event_payload={"__reject__": True, "reason": "用户取消了此操作"},
                )

        # 参数兼容：过滤 LLM 传入的未知参数，校验必填参数
        sig = inspect.signature(tool.handler)
        allowed = set(sig.parameters.keys())
        filtered = {k: v for k, v in payload.items() if k in allowed}
        extra = set(payload.keys()) - allowed
        if extra:
            logger.debug("工具 %s 忽略未知参数: %s", tool_name, extra)

        from src.tools.plan_tools import _set_plan_agent

        missing = {
            name for name, param in sig.parameters.items()
            if param.default is inspect.Parameter.empty and name not in filtered
        }
        if missing:
            result = {
                "error": f"缺少必填参数: {', '.join(sorted(missing))}",
                "error_code": "ArgumentMissing",
                "suggestion": "请参考 arguments_schema 补全必填参数后重试",
                "arguments_schema": tool.arguments_schema,
                "expected_output": tool.expected_output,
            }
        else:
            _set_plan_agent(self)
            try:
                result = tool.handler(**filtered)
            except ToolCallException as e:
                result = {
                    "error": e.message,
                    "error_code": type(e).__name__,
                    "suggestion": e.suggestion,
                    "arguments_schema": tool.arguments_schema,
                    "expected_output": tool.expected_output,
                }
            except Exception as e:
                logger.error("工具 %s 执行失败: %s", tool_name, e)
                result = {
                    "error": str(e),
                    "error_code": type(e).__name__,
                    "arguments_schema": tool.arguments_schema,
                    "expected_output": tool.expected_output,
                }
            finally:
                _set_plan_agent(None)

        logger.debug(
            "工具 %s 结果 — type=%s preview=%s",
            tool_name,
            "error" if isinstance(result, dict) and "error" in result else "ok",
            json.dumps(result, ensure_ascii=False, default=str)[:200],
        )

        # switch 检测：handler 返回 {"__switch__": True, "target": "...", "context": "..."}
        if isinstance(result, dict) and result.get("__switch__"):
            target = result.get("target", "")
            if not target:
                logger.warning("switch handler 缺少 target，忽略切换")
                return Message(
                    role=Role.USER,
                    event_type=EventType.TOOL_CALL_RESULT,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    event_payload={"error": "switch handler 缺少 target 参数"},
                )
            self._pending_switch = (target, result.get("context", ""), tool_call_id)
            return None

        # reject 检测：handler 返回 {"__reject__": True, "reason": "..."}
        if isinstance(result, dict) and result.get("__reject__"):
            self._pending_reject = True

        return Message(
            role=Role.USER,
            event_type=EventType.TOOL_CALL_RESULT,
            tool=tool_name,
            tool_call_id=tool_call_id,
            event_payload=result,
        )

    @staticmethod
    def _format_tool_message(
        tool_name: str,
        payload: dict,
        model_msg: str,
        *,
        confirm: bool,
    ) -> str:
        """格式化工具调用消息，包含模型回复文本、工具名和参数。"""
        params_str = json.dumps(payload, ensure_ascii=False)
        tool_info = f"🔧 {tool_name} {params_str}"
        if confirm:
            tool_info = f"即将执行: {tool_name}\n参数: {params_str}"

        if model_msg:
            return f"{model_msg}\n{tool_info}"
        return tool_info

    def _should_confirm(self, tool: Tool) -> bool:
        """判断工具是否需要审批。不暴露给 LLM。"""
        if tool.confirm_mode == ConfirmMode.NEVER:
            return False
        if tool.confirm_mode == ConfirmMode.ALWAYS:
            return True
        return bool(config.TOOL_CONFIRM_ENABLED)

    def process(self, input: Request) -> Response:
        """Agent 主循环（单步执行，由 App 层驱动循环）。

        每次调用只做一步：处理输入 → LLM 推理 → 分发 → 返回。
        工具执行暂停时返回 PROGRESS，App 喂回 CONTINUE 恢复。

        正常退出由 LLM 返回 ``event_type: "finish"`` 触发。
        达到 ``_max_rounds`` 仍未 finish 时安全阀强制结束。
        """
        agent_name = self._get_agent_name()

        # ── Step 1: 按 RequestType 处理输入 ──
        if input.type == RequestType.USER_INPUT:
            logger.debug("[%s] USER_INPUT: %s", agent_name, input.message[:80])

            # 清理残留状态（安全阀或异常中断时可能残留）
            self._pending_tool = None
            self._pending_switch = None
            self._pending_reject = False
            self._round_counter = 0
            msg = Message(
                role=Role.USER,
                message=input.message,
                event_type=EventType.USER_INPUT,
            )
            self._stamp_plan_status(msg)
            self._history.append(msg)
        elif input.type == RequestType.CONTINUE:
            # _pending_tool 为 None → 跳过工具执行（如切回主 Agent 后的 CONTINUE）
            if self._pending_tool is not None:
                tool_name, payload, tool_call_id = self._pending_tool
                logger.debug("[%s] 执行挂起工具: %s", agent_name, tool_name)
                result_msg = self._execute_tool(tool_name, payload, tool_call_id)
                self._pending_tool = None

                # switch 检测：handler 返回了 __switch__ 标记
                if self._pending_switch:
                    target, context, switch_call_id = self._pending_switch
                    self._pending_switch = None
                    return Response(
                        type=ResponseType.FINISH,
                        message="",
                        switch_agent=target,
                        switch_context=context,
                        switch_tool_call_id=switch_call_id,
                        plan=self._plan,
                    )

                if result_msg is not None:
                    self._stamp_plan_status(result_msg)
                    self._history.append(result_msg)

                # reject 检测：handler 返回了 __reject__ 标记，终止循环等用户输入
                if self._pending_reject:
                    self._pending_reject = False
                    return Response(type=ResponseType.FINISH, message="", plan=self._plan)

        # ── Step 2: LLM 推理 + 分发（内层 while 仅用于错误恢复）──
        self._format_injected = False
        while self._round_counter < self._max_rounds:
            self._round_counter += 1
            logger.debug(
                "[%s] LLM round %d/%d, history=%d msgs",
                agent_name,
                self._round_counter,
                self._max_rounds,
                len(self._history),
            )
            reply = self._llm.chat_pro(self._to_openai(), **self._pro_params)
            logger.debug("[%s] LLM 原始回复 (%d chars):\n%s", agent_name, len(reply), reply)

            # JSON 解析，失败时注入 output_format 让 LLM 自修复
            try:
                llm_msg = self._parse_llm_reply(reply)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(
                    "[%s] JSON parse error (round %d): %s", agent_name, self._round_counter, e
                )
                if not self._format_injected:
                    self._history.append(
                        Message(
                            role=Role.SYSTEM,
                            event_type=EventType.SYSTEM_MESSAGE,
                            message=self._output_format,
                        )
                    )
                    self._format_injected = True
                    logger.debug("[%s] 已注入 output_format 提示", agent_name)
                continue

            logger.debug(
                "[%s] 解析结果 — event_type=%s tool=%s msg_len=%d thinking=%s",
                agent_name,
                llm_msg.event_type,
                llm_msg.tool or "-",
                len(llm_msg.message),
                "有" if llm_msg.thinking else "无",
            )

            # message 为 None 视为格式错误（LLM 输出 null），走 retry
            if llm_msg.message is None:
                logger.warning(
                    "[%s] message 为 None (round %d)，注入 output_format 重试",
                    agent_name, self._round_counter,
                )
                if not self._format_injected:
                    self._history.append(
                        Message(
                            role=Role.SYSTEM,
                            event_type=EventType.SYSTEM_MESSAGE,
                            message=self._output_format,
                        )
                    )
                    self._format_injected = True
                continue

            self._stamp_plan_status(llm_msg)
            self._history.append(llm_msg)

            # ── 事件分发 ──
            # FINISH → 退出
            if llm_msg.event_type == EventType.FINISH:
                logger.debug("[%s] FINISH, round=%d", agent_name, self._round_counter)
                return Response(
                    type=ResponseType.FINISH,
                    message=llm_msg.message,
                    thinking=llm_msg.thinking,
                    plan=self._plan,
                )

            # TOOL_CALL → 工具调度 (7b–7d)
            tool_name = llm_msg.tool or ""

            # 7b. 未知工具 → system_message（附可用工具列表）→ LLM 下轮自修正
            if tool_name not in self._tools:
                logger.warning(
                    "[%s] 未知工具: %s, 可用: %s", agent_name, tool_name, ", ".join(self._tools.keys())
                )
                available = ", ".join(self._tools.keys())
                self._history.append(
                    Message(
                        role=Role.SYSTEM,
                        event_type=EventType.SYSTEM_MESSAGE,
                        message=f"未知工具：{tool_name}。可用工具：{available}",
                    )
                )
                continue

            tool = self._tools[tool_name]
            payload = llm_msg.event_payload or {}
            self._pending_tool = (tool_name, payload, llm_msg.id)

            # 7c. 返回 PROGRESS，App 渲染后自动继续执行工具
            logger.debug("[%s] TOOL_CALL %s → PROGRESS", agent_name, tool_name)
            return Response(
                type=ResponseType.PROGRESS,
                message=self._format_tool_message(
                    tool_name, payload, llm_msg.message, confirm=False
                ),
                thinking=llm_msg.thinking,
                sub_type=EventType.TOOL_CALL,
                plan=self._plan,
            )

        # 安全阀 — 达到最大轮数
        logger.warning("[%s] 达到最大轮数 %d，强制终止", agent_name, self._max_rounds)
        return Response(
            type=ResponseType.FINISH,
            message="已达到最大工具调用轮数，流程终止。",
            plan=self._plan,
        )

    # ── memory ─────────────────────────────────────────────

    def write_memory(
        self,
        conversation: list[Message] | None = None,
        sync_mode: bool = False,
    ):
        """将对话上下文固化为长期记忆。

        封装 ``src.memory.build_memories()``，默认使用当前 Agent 的对话历史。
        默认异步执行（daemon 线程），不阻塞 agent loop。

        Args:
            conversation: 要提取记忆的 Message 列表，默认 ``self._history``。
            sync_mode: True 同步执行并返回 Memory 列表；False daemon 线程后台执行返回 None。

        Returns:
            sync_mode=True 时返回 ``list[Memory]``（可能为空）；sync_mode=False 返回 None。
        """
        from src.memory import build_memories

        conv = conversation if conversation is not None else self._history
        agent = self._get_agent_name()

        if not conv:
            logger.warning("[%s] write_memory: 对话历史为空，跳过", agent)
            return [] if sync_mode else None

        logger.info(
            "[%s] write_memory: %d 条消息, sync=%s", agent, len(conv), sync_mode
        )
        return build_memories(conv, agent=agent, llm=self._llm, sync_mode=sync_mode)
