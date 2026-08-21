from models.tool import ToolCall
from models.result import ToolResult

tc = ToolCall(tool="git_push", arguments={"branch": "main"})
print(tc)

res = ToolResult(success=True, output="Pushed to origin")
print(res)