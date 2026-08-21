from typing import Any, Callable, Dict, Optional

from agent.safety import GIT_CONFIRM_TOOLS, SafetyLayer
from models.tool_result import ToolResult
from tools.registry import TOOLS

ConfirmFn = Callable[[str, Dict[str, Any], str], bool]


class Executor:

    @staticmethod
    def execute(tool_call, confirm_fn: Optional[ConfirmFn] = None) -> ToolResult:
        # confirm_fn defaults to a blocking terminal prompt (CLI usage
        # today), but callers can inject their own — e.g. an MCP server
        # wrapping these tools would supply a different confirmation
        # mechanism instead of blocking on input().
        confirm_fn = confirm_fn or SafetyLayer.cli_confirm

        tool_name = tool_call.tool
        arguments = tool_call.arguments

        requires_confirmation = False
        description = ""

        if tool_name == "run_shell":
            command = arguments.get("command", "")
            if not SafetyLayer.is_shell_command_safe(command):
                requires_confirmation = True
                description = SafetyLayer.describe_shell_command(command)
        elif tool_name in GIT_CONFIRM_TOOLS:
            requires_confirmation = True
            description = SafetyLayer.describe_tool_call(tool_name, arguments)

        if requires_confirmation:
            if not confirm_fn(tool_name, arguments, description):
                return ToolResult(
                    success=False,
                    output="",
                    error="User aborted action requiring confirmation",
                )

        if tool_name not in TOOLS:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}"
            )

        tool = TOOLS[tool_name]

        try:
            return tool.run(**arguments)

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