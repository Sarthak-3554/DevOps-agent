import re

from models.tool_call import ToolCall

DANGEROUS_SHELL_PATTERNS = [
    "rm -rf",
    "sudo",
    "shutdown",
    "reboot",
    "mkfs",
    "pkill",
    "killall",
    "kill -",
    "kill ",
    "dd if=",
    "chmod -r",
    ":(){ :|:& };:"
]

DANGEROUS_TOOLS = {
    "git_push",
    "docker_stop",
    "kill_port",
    "run_shell"
}


class SafetyLayer:

    @staticmethod
    def is_shell_dangerous(command: str) -> bool:
        if not command:
            return False

        normalized = command.lower().strip()
        if any(pattern in normalized for pattern in DANGEROUS_SHELL_PATTERNS):
            return True

        return bool(
            re.search(
                r"(^|[\s;|&])(?:pkill|killall|kill)(?:\s|$|-)",
                normalized,
            )
        )

    @staticmethod
    def is_dangerous(tool_call: ToolCall) -> bool:
        return tool_call.tool in DANGEROUS_TOOLS

    @staticmethod
    def confirm(tool_call: ToolCall) -> bool:
        print("\n⚠️ Dangerous action detected!")
        print(f"Tool: {tool_call.tool}")
        print(f"Arguments: {tool_call.arguments}")

        user_input = input("Do you want to proceed? (y/n): ").strip().lower()
        return user_input == "y"