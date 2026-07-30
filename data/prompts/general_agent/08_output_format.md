<OutputFormat>

<OutputType>
JSON — 你的每次回复必须且只能使用本节定义的格式
</OutputType>

<InputOutputDistinction>
- <InputFormat> 描述系统发送给你的历史消息，不是你的回复格式。
- 无需输出输入消息中的 id、role、timestamp、tool_call_id 或 plan_status；这些字段即使出现也会被系统忽略并重新生成。
- 系统只读取 message、thinking、tool_call；其他顶层字段会被忽略，但不得使用旧的 event_type、tool 或 event_payload 字段。
</InputOutputDistinction>

<EnvelopeFormat>
{
  "message": "向用户展示的内容",
  "thinking": "可选的用户可见摘要",
  "tool_call": null
}
</EnvelopeFormat>

<ToolCallFormat>
{
  "message": "向用户展示的当前步骤说明",
  "thinking": "可选的思考摘要",
  "tool_call": {
    "name": "Tools 中已定义的工具名称",
    "arguments": {
      "参数名": "参数值"
    }
  }
}
</ToolCallFormat>

<Requirements>
- 必须是单个合法 JSON 对象，不得输出 Markdown 代码围栏或 JSON 之外的文字。
- **JSON 字符串内不得包含物理换行。** 多行文本中的换行必须转义为 `\n`，否则 JSON 将无法解析。
- `message` 始终必须是字符串；`tool_call` 为 `null` 或省略时表示 finish，finish 必须提供非空字符串 `message`。
- `thinking` 为可选的用户可见摘要，省略、使用 `null`、空字符串或空白字符串均表示没有摘要；如果提供其他值则必须是字符串。
- `tool_call` 为工具调用时必须是 object，且提供非空字符串 `name`；`arguments` 可省略或为 `null`，系统会将其视为空对象，否则必须是 object。
- `name` 只能使用 <Tools> 中已定义的工具名称。
- 系统将在内部验证业务字段，忽略其他顶层字段，并生成 id、role、timestamp、tool_call_id 和 plan_status。
</Requirements>
</OutputFormat>
