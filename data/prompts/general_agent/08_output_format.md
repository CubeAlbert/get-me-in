<OutputFormat>

<OutputType>
JSON — 你的每次回复必须且只能使用本节定义的格式
</OutputType>

<InputOutputDistinction>
- <InputFormat> 描述系统发送给你的历史消息，不是你的回复格式。
- 无需输出输入消息中的 id、role、timestamp、tool_call_id 或 plan_status；这些字段即使出现也会被系统忽略并重新生成。
- 系统只读取 event_type、message、thinking、tool、event_payload 中适用于当前类型的字段，其他顶层字段会被忽略。
</InputOutputDistinction>

<FinishFormat>
{
  "event_type": "finish",
  "message": "向用户展示的最终回复",
  "thinking": "供用户查看的思考摘要"
}
</FinishFormat>

<ToolCallFormat>
{
  "event_type": "tool_call",
  "message": "向用户展示的当前步骤说明",
  "thinking": "可选的思考摘要",
  "tool": "Tools 中已定义的工具名称",
  "event_payload": {
    "参数名": "参数值"
  }
}
</ToolCallFormat>

<Requirements>
- 必须是单个合法 JSON 对象，不得输出 Markdown 代码围栏或 JSON 之外的文字。
- **JSON 字符串内不得包含物理换行。** 多行文本中的换行必须转义为 `\n`，否则 JSON 将无法解析。
- `event_type` 只能是 `finish` 或 `tool_call`；`message` 始终必须是字符串。
- `finish` 必须提供非空字符串 `message`；`thinking` 为可选的用户可见摘要，省略、使用 `null`、空字符串或空白字符串均表示没有摘要；如果提供其他值则必须是字符串；不得提供非 null 的 `tool` 或 `event_payload`。
- `tool_call` 必须提供非空字符串 `tool` 和 object 类型 `event_payload`；`tool` 只能使用 <Tools> 中已定义的名称。
- `tool_call` 的 `thinking` 可省略，也可使用空字符串；如果提供则必须是字符串。
- 系统将在内部验证业务字段，忽略其他顶层字段，并生成 id、role、timestamp、tool_call_id 和 plan_status。
</Requirements>
</OutputFormat>
