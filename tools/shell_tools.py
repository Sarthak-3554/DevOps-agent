from pydantic import BaseModel, Field

from models.tool_result import ToolResult
from tools.base import BaseTool
from tools.sandbox import Sandbox


class ShellArgs(BaseModel):
    command: str = Field(..., description="The exact shell command to execute")


class ShellTool(BaseTool):
    name = "run_shell"
    description = (
        "Run an arbitrary shell command inside an isolated sandbox "
        "container (not the host machine). Last-resort tool: only use "
        "this when no specific tool (git_push, git_status, git_checkout, "
        "git_pull, git_remote_add) already covers the requested action."
    )
    args_schema = ShellArgs

    def __init__(self):
        # One Sandbox (and one docker client) per ShellTool instance,
        # reused across calls — each individual command still runs in
        # its own fresh, disposable container.
        self._sandbox = Sandbox()

    def run(self, command: str) -> ToolResult:
        return self._sandbox.run(command)