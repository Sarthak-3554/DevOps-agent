import unittest
from unittest.mock import patch

from agent.executor import Executor
from models.tool_call import ToolCall
from models.tool_result import ToolResult


class ExecutorTests(unittest.TestCase):
    def test_unknown_tool_returns_failure(self):
        call = ToolCall(id="call_1", tool="does_not_exist", arguments={})

        result = Executor.execute(call)

        self.assertFalse(result.success)
        self.assertIn("Unknown tool", result.error)

    def test_invalid_arguments_return_failure_not_exception(self):
        # git_status takes no arguments — this mirrors the real hallucinated
        # call we saw in practice ({'branch': None, 'remote': None}).
        call = ToolCall(
            id="call_1",
            tool="git_status",
            arguments={"branch": None, "remote": None},
        )

        result = Executor.execute(call)

        self.assertFalse(result.success)
        self.assertIn("Invalid arguments", result.error)

    @patch("agent.executor.TOOLS")
    def test_successful_tool_call_returns_success_result(self, mock_tools):
        mock_tool = mock_tools.__getitem__.return_value
        mock_tool.run.return_value = ToolResult(success=True, output="On branch main")
        mock_tools.__contains__.return_value = True

        call = ToolCall(id="call_1", tool="git_status", arguments={})
        result = Executor.execute(call)

        self.assertTrue(result.success)
        self.assertEqual(result.output, "On branch main")

    def test_dangerous_shell_command_without_confirmation_is_blocked(self):
        call = ToolCall(id="call_1", tool="run_shell", arguments={"command": "sudo rm -rf /"})

        result = Executor.execute(call, confirm_fn=lambda *args: False)

        self.assertFalse(result.success)
        self.assertIn("aborted", result.error.lower())

    def test_unrecognized_shell_command_also_requires_confirmation(self):
        # Not on the safe allowlist, but not obviously destructive either
        # — this is the default-deny case the allowlist model is for.
        call = ToolCall(id="call_1", tool="run_shell", arguments={"command": "curl https://example.com"})

        result = Executor.execute(call, confirm_fn=lambda *args: False)

        self.assertFalse(result.success)
        self.assertIn("aborted", result.error.lower())

    @patch("agent.executor.TOOLS")
    def test_safe_shell_command_runs_without_prompting(self, mock_tools):
        mock_tool = mock_tools.__getitem__.return_value
        mock_tool.run.return_value = ToolResult(success=True, output="file1\nfile2")
        mock_tools.__contains__.return_value = True

        def confirm_should_not_be_called(*args):
            raise AssertionError("confirm_fn should not be called for a safe command")

        call = ToolCall(id="call_1", tool="run_shell", arguments={"command": "ls"})
        result = Executor.execute(call, confirm_fn=confirm_should_not_be_called)

        self.assertTrue(result.success)

    @patch("agent.executor.TOOLS")
    def test_git_push_always_requires_confirmation(self, mock_tools):
        mock_tool = mock_tools.__getitem__.return_value
        mock_tool.run.return_value = ToolResult(success=True, output="pushed")
        mock_tools.__contains__.return_value = True

        call = ToolCall(id="call_1", tool="git_push", arguments={"remote": "origin", "branch": "main"})

        blocked = Executor.execute(call, confirm_fn=lambda *args: False)
        self.assertFalse(blocked.success)
        self.assertIn("aborted", blocked.error.lower())

        allowed = Executor.execute(call, confirm_fn=lambda *args: True)
        self.assertTrue(allowed.success)

    @patch("agent.executor.TOOLS")
    def test_git_status_does_not_require_confirmation(self, mock_tools):
        mock_tool = mock_tools.__getitem__.return_value
        mock_tool.run.return_value = ToolResult(success=True, output="clean")
        mock_tools.__contains__.return_value = True

        def confirm_should_not_be_called(*args):
            raise AssertionError("confirm_fn should not be called for git_status")

        call = ToolCall(id="call_1", tool="git_status", arguments={})
        result = Executor.execute(call, confirm_fn=confirm_should_not_be_called)

        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()