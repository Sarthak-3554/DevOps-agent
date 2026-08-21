from tools.git_tools import (
    GitPushTool,
    GitStatusTool,
    GitRemoteAddTool,
    GitCheckoutTool,
    GitPullTool
)
from tools.shell_tools import ShellTool

TOOLS = {
    "git_push": GitPushTool(),
    "git_status": GitStatusTool(),
    "git_remote_add": GitRemoteAddTool(),
    "git_checkout": GitCheckoutTool(),
    "git_pull": GitPullTool(),
    "run_shell": ShellTool(),
}

# OpenAI/litellm-style tool schemas, derived once from each tool's
# args_schema (see tools/base.py). Pass this straight into
# LLM.chat(messages, tools=TOOL_SCHEMAS) — nothing here is hand-duplicated
# in prompts.py anymore.
TOOL_SCHEMAS = [tool.__class__.schema() for tool in TOOLS.values()]
