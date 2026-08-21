import time
from typing import Any, Callable, Dict, Optional

from agent.logger import AuditLogger
from agent.safety import GIT_CONFIRM_TOOLS, SafetyLayer
from models.tool_result import ToolResult
from tools.registry import TOOLS

ConfirmFn = Callable[[str, Dict[str, Any], str], bool]


class Executor:

    @staticmethod
    def execute(
        tool_call,
        confirm_fn: Optional[ConfirmFn] = None,
        logger: Optional[AuditLogger] = None,
        session_id: str = "",
    ) -> ToolResult:
        # confirm_fn defaults to a blocking terminal prompt (CLI usage
        # today), but callers can inject their own — e.g. an MCP server
        # wrapping these tools would supply a different confirmation
        # mechanism instead of blocking on input().
        confirm_fn = confirm_fn or SafetyLayer.cli_confirm

        tool_name = tool_call.tool
        arguments = tool_call.arguments
        start = time.monotonic()

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

        confirmed: Optional[bool] = None

        if requires_confirmation:
            confirmed = confirm_fn(tool_name, arguments, description)
            if not confirmed:
                result = ToolResult(
                    success=False,
                    output="",
                    error="User aborted action requiring confirmation",
                )
                Executor._log(
                    logger, session_id, tool_name, arguments,
                    requires_confirmation, confirmed, result, start,
                )
                return result

        if tool_name not in TOOLS:
            result = ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {tool_name}"
            )
            Executor._log(
                logger, session_id, tool_name, arguments,
                requires_confirmation, confirmed, result, start,
            )
            return result

        tool = TOOLS[tool_name]

        try:
            result = tool.run(**arguments)

        except TypeError as e:
            result = ToolResult(
                success=False,
                output="",
                error=f"Invalid arguments for tool {tool_name}: {str(e)}"
            )

        except Exception as e:
            result = ToolResult(
                success=False,
                output="",
                error=str(e)
            )

        Executor._log(
            logger, session_id, tool_name, arguments,
            requires_confirmation, confirmed, result, start,
        )
        return result

    @staticmethod
    def _log(logger, session_id, tool_name, arguments, requires_confirmation, confirmed, result, start):
        if logger is None:
            return
        logger.log_tool_call(
            session_id=session_id,
            tool=tool_name,
            arguments=arguments,
            sandboxed=(tool_name == "run_shell"),
            required_confirmation=requires_confirmation,
            confirmed=confirmed,
            success=result.success,
            error=result.error,
            duration_ms=(time.monotonic() - start) * 1000,
        )