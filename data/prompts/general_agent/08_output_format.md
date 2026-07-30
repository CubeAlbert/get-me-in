<OutputFormat>

<OutputType>
JSON — 你的每次回复必须且只能使用本节定义的格式
</OutputType>

<InputOutputDistinction>
- <InputFormat> 描述系统发送给你的历史消息，不是你的回复格式。
- 你的回复只需提供 event_type、message、thinking、tool 和 event_payload；不需要复制输入消息中的 id、role、timestamp、tool_call_id 或 plan_status。
- event_type=finish 时使用 finish 格式；event_type=tool_call 时使用 tool_call 格式。系统会为事件补齐内部字段并验证工具名称。
</InputOutputDistinction>

<FinishFormat>
{
  "event_type": "finish",
  "message": "向用户展示的最终回复",
  "thinking": "通常应尽量提供简短、非空、用户可见的摘要",
  "tool": null,
  "event_payload": null
}
</FinishFormat>

<ToolCallFormat>
{
  "event_type": "tool_call",
  "message": "向用户展示的当前步骤说明",
  "thinking": "可选的用户可见摘要",
  "tool": "Tools 中已定义的工具名称",
  "event_payload": {
    "参数名": "参数值"
  }
}
</ToolCallFormat>

<Requirements>
- 必须是单个合法 JSON 对象，不得输出 Markdown 代码围栏或 JSON 之外的文字。
- JSON 字符串内不得包含物理换行。多行文本中的换行必须转义为 \n，否则 JSON 将无法解析。
- event_type 必须是 `finish` 或 `tool_call`。
- finish 必须提供非空字符串 message；tool 和 event_payload 应省略或为 null。thinking 可省略、为 null、空字符串或空白字符串；如果提供其他值则必须是字符串。
- tool_call 必须提供字符串 message、非空字符串 tool 和 object event_payload；thinking 可省略、为 null、空字符串或空白字符串；如果提供其他值则必须是字符串。
- tool 只能使用 <Tools> 中已定义的工具名称；工具参数必须直接放在 event_payload 中。
- 系统会忽略其他顶层字段，并重新生成 id、role、timestamp、tool_call_id 和 plan_status；不要依赖或伪造这些字段。
</Requirements>
</OutputFormat>
