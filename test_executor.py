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

        with patch("agent.safety.SafetyLayer.confirm", return_value=False):
            result = Executor.execute(call)

        self.assertFalse(result.success)
        self.assertIn("aborted", result.error.lower())


if __name__ == "__main__":
    unittest.main()