from models import tool_call
from tools.registry import TOOLS
from models.tool_result import ToolResult
from models.tool_call import ToolCall as ToolCallModel
from agent.safety import SafetyLayer


class Executor:

    @staticmethod
    def execute(tool_call):

        tool_name = tool_call.tool
        # 🔥 Special handling for shell tool
        if tool_name == "run_shell":
            command = tool_call.arguments.get("command", "")

            if SafetyLayer.is_shell_dangerous(command):
                if not SafetyLayer.confirm(
                    ToolCallModel(
                        tool=tool_name,
                        arguments={"command": command},
                    )
                ):
                    return ToolResult(
                        success=False,
                        output="",
                        error="User aborted dangerous command"
                    )
        # ✅ Handle unknown tool
        if tool_name not in TOOLS:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}"
            )

        tool = TOOLS[tool_name]

        try:
            return tool.run(**tool_call.arguments)

        except TypeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid arguments for tool {tool_name}: {str(e)}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )