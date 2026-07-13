<OutputFormat>

<OutputType>
JSON
</OutputType>

<Schema>
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "随机生成的 UUID v4 格式（例：550e8400-e29b-41d4-a716-446655440000）"
    },
    "role": {
      "const": "assistant",
      "description": "固定为 assistant"
    },
    "thinking": {
      "type": "string",
      "description": "LLM 内部推理过程。event_type 为 finish 时必填，tool_call 时可省略"
    },
    "event_type": {
      "type": "string",
      "enum": ["tool_call", "finish"],
      "description": "tool_call=需要调用工具 | finish=无需工具调用，message 即为最终消息"
    },
    "message": {
      "type": "string",
      "description": "向用户展示当前步骤的文本"
    },
    "tool": {
      "type": ["string", "null"],
      "description": "调用的工具名，event_type 为 finish 时必须为 null"
    },
    "event_payload": {
      "type": ["object", "null"],
      "description": "工具参数。仅需提供已声明的参数，多余参数会被忽略，但必填参数不得缺失。event_type 为 finish 时必须为 null"
    }
  },
  "required": ["id", "role", "event_type", "message"]
}
</Schema>
<Requirements>
- 必须是合法的 JSON，严格符合上述 Schema。
- **JSON 字符串内不得包含物理换行。** 多行文本中的换行必须转义为 `\n`，否则 JSON 将无法解析。
- `tool` 只能使用 <Tools> 中已定义的工具名称。
</Requirements>
</OutputFormat>
