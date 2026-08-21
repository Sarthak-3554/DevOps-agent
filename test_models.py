from models.tool_call import ToolCall
from models.tool_result import ToolResult

tc = ToolCall(tool="git_push", arguments={"branch": "main"})
print(tc)

res = ToolResult(success=True, output="Pushed to origin")
print(res)