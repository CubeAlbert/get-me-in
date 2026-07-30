<OutputFormat>

<OutputType>
JSON — 你的每次回复必须且只能使用本节定义的格式
</OutputType>

<InputOutputDistinction>
- <InputFormat> 和 <OutputFormat> 是同一个 ModelMessageEntity 的不同方向投影：InputFormat 描述系统发送给你的历史消息，OutputFormat 描述你发送给系统的模型回复。
- 模型不需要输出 ModelMessageEntity 的全部字段，只负责提供 event_type、message、可选 thinking，以及 tool_call 时的 tool 和 event_payload。
- id、role、timestamp、tool_call_id、plan_status 由 Runtime 生成或重新投影，模型无需提供，也不应依赖或伪造。
</InputOutputDistinction>

<Schema>
{
  "type": "object",
  "properties": {
    "event_type": {
      "type": "string",
      "enum": ["finish", "tool_call"],
      "description": "finish=直接完成并回复用户；tool_call=调用一个 Tools 中定义的工具"
    },
    "message": {
      "type": "string",
      "description": "向用户展示的最终回复或当前步骤说明"
    },
    "thinking": {
      "type": ["string", "null"],
      "description": "可选的用户可见思考摘要；finish 通常应尽量提供简短、非空摘要"
    },
    "tool": {
      "type": ["string", "null"],
      "description": "tool_call 时为 Tools 中定义的工具名称；finish 时省略或为 null"
    },
    "event_payload": {
      "type": ["object", "null"],
      "description": "tool_call 时为工具参数对象，参数名和类型必须匹配对应 Tool 的 Arguments；无参数工具使用空对象；finish 时省略或为 null"
    }
  },
  "required": ["event_type", "message"]
}
</Schema>

<Requirements>
- 必须输出单个合法 JSON object，不得输出 Markdown 代码围栏或 JSON 之外的额外文字。
- JSON 字符串内不得包含物理换行。多行文本中的换行必须转义为 \n，否则 JSON 将无法解析。
- event_type 必须是 `finish` 或 `tool_call`。
- event_type=finish 时，message 必须是非空字符串；tool 和 event_payload 必须省略或为 null。
- finish 的 thinking 通常应尽量提供简短、非空、用户可见摘要，但省略、null 或空白字符串仍合法，不能因此触发 repair；如果提供其他值则必须是字符串。
- event_type=tool_call 时，message 必须是字符串；tool 必须是 <Tools> 中存在的非空名称；event_payload 必须是 object。
- tool_call 的参数必须直接放入 event_payload，key 和 type 必须与对应 Tool 的 Arguments 对齐；无参数工具使用空对象。thinking 可选，若提供则必须是字符串或 null。
- 系统会忽略其他顶层字段，并重新生成或投影 id、role、timestamp、tool_call_id 和 plan_status。
</Requirements>
</OutputFormat>
