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
      "const": "user",
      "description": "固定为 user"
    },
    "timestamp": {
      "type": "string",
      "description": "ISO 8601 时间戳"
    },
    "event_type": {
      "type": "string",
      "enum": ["user_input", "tool_call_result", "system_message"],
      "description": "事件类型"
    },
    "message": {
      "type": "string",
      "description": "消息文本内容，tool_call_result 时可能为空或包含 stdout"
    },
    "tool": {
      "type": ["string", "null"],
      "description": "工具名，仅 tool_call_result 时填写"
    },
    "tool_call_id": {
      "type": ["string", "null"],
      "description": "对应 tool_call 消息的 id，仅 tool_call_result 时填写"
    },
    "event_payload": {
      "type": ["object", "null"],
      "description": "工具调用结果：正常时为工具返回的结构化数据；错误时为 {error, error_code, suggestion?, arguments_schema, expected_output}"
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
- `user_input` — 用户输入
- `tool_call_result` — 工具调用结果（系统注入）。`tool` 和 `tool_call_id` 标识来源工具调用。`event_payload` 正常时为工具返回的结构化数据；工具执行失败时格式为 `{"error": "<错误描述>", "error_code": "<异常类型名>", "suggestion": "<修复建议|null>", "arguments_schema": "<工具参数schema>", "expected_output": "<期望输出格式>"}`。收到错误后应先用 suggestion 和 arguments_schema 修复参数后重试，不要重复构造相同的错误调用。`message` 可能为空或包含 stdout。
- `system_message` — 系统提示/错误恢复
</EventTypes>

</InputFormat>
