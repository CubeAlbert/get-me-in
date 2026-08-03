<OutputFormat>

<OutputType>
JSON — 你的每次回复必须且只能使用本节定义的格式
</OutputType>

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
      "minLength": 1,
      "description": "向用户展示的最终回复或当前执行步骤说明，可以使用 Markdown"
    },
    "thinking": {
      "type": "string",
      "description": "finish 事件必须提供的简短、用户可见纯文本思考摘要，不使用 Markdown"
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
- 必须且只能输出一个符合上述 Schema 的合法 JSON object。
- 无论 event_type 为 finish 还是 tool_call，都必须提供 message；message 必须是非空、非纯空白字符串，用于向用户说明最终回复或当前执行步骤，可以使用 Markdown。
- event_type=finish 时，必须提供 thinking；thinking 必须是纯文本字符串，不使用 Markdown，并应尽量简短、适合直接向用户展示。tool 和 event_payload 必须省略或为 null。
- event_type=tool_call 时，tool 必须是 <Tools> 中存在的非空名称；event_payload 必须是 object。
- tool_call 的参数必须直接放入 event_payload，key 和 type 必须与对应 Tool 的 Arguments 对齐；无参数工具使用空对象。
- 无需提供 id、role、timestamp、tool_call_id 或 plan_status。
</Requirements>
</OutputFormat>
