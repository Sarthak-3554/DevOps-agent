import re
from typing import Any, Dict

# Commands considered safe to run without confirmation: read-only, no
# side effects on the filesystem or repo state. This is an ALLOWLIST,
# not a blocklist — anything NOT matched here requires confirmation by
# default, even if it doesn't "look" dangerous. Default-deny, not
# default-allow. This is the direct fix for the old blocklist's failure
# mode: a blocklist only stops patterns someone thought to list, so
# anything novel or slightly reworded slipped through silently.
SAFE_SHELL_PREFIXES = (
    "ls",
    "pwd",
    "cat ",
    "echo ",
    "whoami",
    "git status",
    "git log",
    "git diff",
    "df ",
    "du ",
    "which ",
    "python --version",
    "python3 --version",
    "node --version",
    "npm --version",
)

# Characters that let a "safe" command smuggle in another command via
# chaining, piping, or substitution (e.g. "ls; rm -rf /",
# "ls $(rm -rf /)"). Any of these disqualifies a command from
# auto-approval, even if it starts with an allowlisted prefix — otherwise
# the allowlist itself becomes the bypass.
SHELL_CHAINING_PATTERN = re.compile(r"[;&|`]|\$\(")

# Tools that always require confirmation regardless of arguments — these
# mutate remote or local repo state in ways that aren't easily undone
# (force pushes, switching branches over uncommitted work, etc).
GIT_CONFIRM_TOOLS = {"git_push", "git_checkout"}


class SafetyLayer:

    @staticmethod
    def is_shell_command_safe(command: str) -> bool:
        """
        True only for commands that are both (a) read-only per the
        allowlist and (b) not chained with anything else. Everything
        else — including commands we simply don't recognize — requires
        confirmation.
        """
        if not command:
            return False

        normalized = command.strip()

        if SHELL_CHAINING_PATTERN.search(normalized):
            return False

        return any(
            normalized == prefix.strip() or normalized.startswith(prefix)
            for prefix in SAFE_SHELL_PREFIXES
        )

    @staticmethod
    def describe_shell_command(command: str) -> str:
        return f"Run inside the sandbox: {command}"

    @staticmethod
    def describe_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "git_push":
            remote = arguments.get("remote", "origin")
            branch = arguments.get("branch", "main")
            return f"Push local commits to '{remote}/{branch}'."
        if tool_name == "git_checkout":
            branch = arguments.get("branch", "?")
            return f"Check out branch '{branch}' (uncommitted changes may be affected)."
        return f"Run {tool_name} with arguments {arguments}."

    @staticmethod
    def cli_confirm(tool_name: str, arguments: Dict[str, Any], description: str) -> bool:
        """
        Default confirmation UI: a blocking terminal prompt. Executor
        accepts a confirm_fn override so this isn't hardwired to CLI use
        — e.g. an MCP server wrapping these tools later would supply its
        own confirmation mechanism instead.
        """
        print("\n⚠️  Confirmation required")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")
        print(f"Effect: {description}")

        answer = input("Proceed? (y/n): ").strip().lower()
        return answer == "y"