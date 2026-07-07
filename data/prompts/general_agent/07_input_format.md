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
      "description": "工具调用结果，仅 tool_call_result 时填写"
    }
  },
  "required": ["id", "role", "timestamp", "event_type", "message"]
}
</Schema>

<EventTypes>
- `user_input` — 用户输入
- `tool_call_result` — 工具调用结果（系统注入）。`tool` 和 `tool_call_id` 标识来源工具调用，`event_payload` 为工具返回的结构化数据，`message` 可能为空或包含 stdout。
- `system_message` — 系统提示/错误恢复
</EventTypes>

</InputFormat>
