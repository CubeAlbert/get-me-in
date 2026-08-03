<InputFormat>

<InputType>
JSON — 对话历史中每条消息均为一个 JSON 对象
</InputType>

<Schema>
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "消息唯一标识（UUID v4）"
    },
    "role": {
      "type": "string",
      "enum": ["user", "assistant", "system"],
      "description": "发送者角色。user=用户输入/工具结果 | assistant=LLM 自身历史回复 | system=系统纠错消息"
    },
    "timestamp": {
      "type": "string",
      "description": "ISO 8601 时间戳"
    },
    "event_type": {
      "type": "string",
      "enum": ["user_input", "tool_call_result", "system_message", "tool_call", "finish"],
      "description": "事件类型。user_input/tool_call_result/system_message 的 role 为 user 或 system；tool_call/finish 的 role 为 assistant（LLM 自身历史回复，不包含 thinking 字段）"
    },
    "message": {
      "type": "string",
      "description": "消息文本内容，tool_call_result 时可能为空或包含 stdout"
    },
    "tool": {
      "type": ["string", "null"],
      "description": "工具名，仅 tool_call 和 tool_call_result 时填写"
    },
    "tool_call_id": {
      "type": ["string", "null"],
      "description": "工具调用链标识；tool_call 及其对应的 tool_call_result 使用同一 UUID"
    },
    "event_payload": {
      "type": ["object", "null"],
      "description": "tool_call 时为工具参数；tool_call_result 时为结构化结果或错误信息"
    },
    "plan_status": {
      "type": ["object", "null"],
      "description": "当前计划状态（系统注入，仅参考）。无计划时为 null。结构：{current: \"序号|任务名\" | null, completed: [\"序号|任务名\"], remaining: [\"序号|任务名\"]}。序号为从 0 开始递增的数字。你应该根据 current 和 remaining 推进任务，完成后自行调用合适的工具更新计划状态。"
    }
  },
  "required": ["id", "role", "timestamp", "event_type", "message"]
}
</Schema>

<EventTypes>
- `user_input` — 用户输入（role=user）
- `tool_call_result` — 工具调用结果（系统注入，role=user）。`tool` 和 `tool_call_id` 标识来源工具调用。`event_payload` 正常时为工具返回的结构化数据；工具执行失败时格式为 `{"error": "<错误描述>", "error_code": "<异常类型名>", "suggestion": "<修复建议|null>", "arguments_schema": "<工具参数schema>", "expected_output": "<期望输出格式>"}`。收到错误后应先用 suggestion 和 arguments_schema 修复参数后重试，不要重复构造相同的错误调用。`message` 可能为空或包含 stdout。
- `system_message` — 系统提示/错误恢复（role=system 或 user）。如 output_format 注入、未知工具提示等。
- `tool_call` — LLM 自身历史工具调用（role=assistant）。`id` 是消息事件 UUID，`tool_call_id` 是工具调用链 UUID；`message` 为工具调用说明文本，`tool` 为调用的工具名，`event_payload` 为工具参数。**不含 `thinking` 字段**（系统已剥离）。
- `finish` — LLM 自身历史最终回复（role=assistant）。`message` 为最终回复文本，`tool` 和 `event_payload` 均为 null。**不含 `thinking` 字段**（系统已剥离）。
</EventTypes>

</InputFormat>
