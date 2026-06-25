<Tools>

<Tool name="ask_user">
<Purpose>
向用户请求额外信息。
</Purpose>
<UseWhen>
- 缺少必要信息。
- 需要用户确认。
- 存在多个方案需要用户选择。
- 风险操作需要获得批准。
</UseWhen>
<DoNotUseWhen>
- 可以通过已有信息继续完成任务。
</DoNotUseWhen>
<Arguments>
{
  "message": "string (Markdown格式文本)"
}
</Arguments>
<ExpectedOutput>
- 无输出
- Runtime进入 WAITING_FOR_USER 状态
</ExpectedOutput>
</Tool>

<Tool name="finish">
<Purpose>
结束当前Agent执行流程并向用户返回最终结果。
</Purpose>
<UseWhen>
- 当前任务已经完成。
- 当前问题已经得到最终回答。
- Agent不再需要执行任何后续动作。
</UseWhen>
<DoNotUseWhen>
- 仍需用户提供额外信息。
- 仍需调用其他工具。
- 仍需继续推理。
</DoNotUseWhen>
<Arguments>
{
  "message": "string (Markdown格式文本)"
}
</Arguments>
<ExpectedOutput>
- 无输出
- Runtime结束本次执行
</ExpectedOutput>
</Tool>

<Tool name="return">
<Purpose>
子Agent退出并把结果返回给父Agent
</Purpose>
<UseWhen>
- 用户显式提出不再继续流程。
- 用户显式提出需要返回到主界面/主入口/主程序。
- 用户要求任务执行完毕后退出并且当前Agent不再需要执行任何后续动作。
</UseWhen>
<DoNotUseWhen>
- 当前为主Agent。
- 仍需用户提供额外信息。
- 仍需调用其他工具。
- 仍需继续推理。
</DoNotUseWhen>
<Arguments>
{
  "message": "completed"
}
</Arguments>
<ExpectedOutput>
- 无
</ExpectedOutput>
</Tool>

{{ADDITION_TOOLS}}
</Tools>