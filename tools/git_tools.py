import subprocess

from pydantic import BaseModel, Field

from models.tool_result import ToolResult
from tools.base import BaseTool


class GitPushArgs(BaseModel):
    remote: str = Field("origin", description="Git remote to push to")
    branch: str = Field("main", description="Branch to push")


class GitPushTool(BaseTool):
    name = "git_push"
    description = "Push local commits on a branch to a remote repository."
    args_schema = GitPushArgs

    def run(self, remote: str = "origin", branch: str = "main") -> ToolResult:
        try:
            cmd = ["git", "push", remote, branch]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class GitStatusArgs(BaseModel):
    pass


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Show the working tree status of the current git repository."
    args_schema = GitStatusArgs

    def run(self) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "status"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class GitRemoteAddArgs(BaseModel):
    remote: str = Field("origin", description="Name to give the remote")
    url: str = Field(..., description="Repository URL to add as a remote")


class GitRemoteAddTool(BaseTool):
    name = "git_remote_add"
    description = "Add a new git remote pointing at a repository URL."
    args_schema = GitRemoteAddArgs

    def run(self, url: str, remote: str = "origin") -> ToolResult:
        try:
            if not url:
                return ToolResult(
                    success=False,
                    output="",
                    error="Repository URL is required"
                )

            result = subprocess.run(
                ["git", "remote", "add", remote, url],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output="Remote added successfully")

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class GitCheckoutArgs(BaseModel):
    branch: str = Field(..., description="Branch name to check out")


class GitCheckoutTool(BaseTool):
    name = "git_checkout"
    description = "Check out an existing local or remote-tracking git branch."
    args_schema = GitCheckoutArgs

    def run(self, branch: str) -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "checkout", branch],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class GitPullArgs(BaseModel):
    remote: str = Field("origin", description="Git remote to pull from")
    branch: str = Field("main", description="Branch to pull")


class GitPullTool(BaseTool):
    name = "git_pull"
    description = "Pull the latest changes for a branch from a remote repository."
    args_schema = GitPullArgs

    def run(self, remote: str = "origin", branch: str = "main") -> ToolResult:
        try:
            result = subprocess.run(
                ["git", "pull", remote, branch],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return ToolResult(success=True, output=result.stdout)

            return ToolResult(success=False, output="", error=result.stderr)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
