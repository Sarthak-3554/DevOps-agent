import subprocess

from pydantic import BaseModel, Field

from models.tool_result import ToolResult
from tools.base import BaseTool


class ShellArgs(BaseModel):
    command: str = Field(..., description="The exact shell command to execute")


class ShellTool(BaseTool):
    name = "run_shell"
    description = (
        "Run an arbitrary shell command. Last-resort tool: only use this "
        "when no specific tool (git_push, git_status, git_checkout, "
        "git_pull, git_remote_add) already covers the requested action."
    )
    args_schema = ShellArgs

    def run(self, command: str) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
