<OutputFormat>

<ResponseType>
JSON
</ResponseType>

<Schema>
{
  "thinking":"...",
  "action": {
    "id": "uuid (随机生成)",
    "tool": "...",
    "message": "...",
    "args": {}
  }
}
</Schema>
<Requirements>
- 必须是合法的 JSON。
- 不允许有额外的字段属性。
- 必须包含 `thinking` 和 `action` 属性。
- `action.id` 必须是随机生成的符合 UUID v4 格式的字符串。
- `action.tool` 只能使用 <Tools> 中已定义的工具名称。
- `action.message` 必须填写，用于向用户展示当前步骤的决策或结果。
- 当 `action.tool` 为 `ask_user` 或 `finish` 时，`message` 即为展示给用户的最终消息。
</Requirements>
</OutputFormat>