import unittest
from unittest.mock import patch
from agent.agent import Agent, _truncate_for_model, MAX_TOOL_RESULT_CHARS
from models.llm_response import LLMResponse
from models.tool_call import ToolCall


class TruncationTests(unittest.TestCase):
    def test_short_output_is_untouched(self):
        text = "On branch main\nnothing to commit"
        self.assertEqual(_truncate_for_model(text), text)

    def test_long_output_is_truncated_with_a_note(self):
        # Regression test for the real failure: an apt-get install's full
        # log (hundreds of lines) got sent back to the model verbatim,
        # and the resulting message history blew past Groq's 8k TPM
        # rate limit on the very next turn.
        text = "x" * (MAX_TOOL_RESULT_CHARS + 5000)

        result = _truncate_for_model(text)

        self.assertLess(len(result), len(text))
        self.assertIn("truncated", result)
        self.assertTrue(result.startswith("x" * 100))  # real content preserved up front


class AgentLoopTests(unittest.TestCase):
    @patch("agent.executor.Executor.execute")
    @patch("llm.litellm_provider.LiteLLMProvider.chat")
    def test_does_not_declare_success_after_a_merely_successful_remedial_step(
        self, mock_chat, mock_execute
    ):
        """
        Regression test for the real bug we hit: user asks for `git add .`,
        it fails because git isn't installed, the model installs git
        (which succeeds), and the OLD harness declared the whole task
        done right there — without git add . ever actually running again.
        The fix: only a plain-text, no-tool-calls response ends the loop.
        """
        from models.tool_result import ToolResult

        mock_chat.side_effect = [
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="c1", tool="run_shell", arguments={"command": "git add ."})],
            ),
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="c2", tool="run_shell", arguments={"command": "apt-get install -y git"})],
            ),
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="c3", tool="run_shell", arguments={"command": "git add ."})],
            ),
            LLMResponse(content="Done — changes staged.", tool_calls=[]),
        ]

        mock_execute.side_effect = [
            ToolResult(success=False, output="", error="git: not found"),
            ToolResult(success=True, output="git installed"),  # remedial step succeeds
            ToolResult(success=True, output=""),                # the actual retried action
        ]

        agent = Agent()
        agent.run("do git add .")

        # The critical assertion: the loop must have gone all the way to
        # turn 4 (the plain-text completion) rather than stopping after
        # turn 2 just because installing git succeeded.
        self.assertEqual(mock_chat.call_count, 4)
        self.assertEqual(mock_execute.call_count, 3)

    @patch("agent.executor.Executor.execute")
    @patch("llm.litellm_provider.LiteLLMProvider.chat")
    def test_stops_immediately_on_first_plain_text_response(self, mock_chat, mock_execute):
        mock_chat.side_effect = [
            LLMResponse(content="No git operation needed here.", tool_calls=[]),
        ]

        agent = Agent()
        agent.run("what's up")

        self.assertEqual(mock_chat.call_count, 1)
        mock_execute.assert_not_called()

    @patch("agent.executor.Executor.execute")
    @patch("llm.litellm_provider.LiteLLMProvider.chat")
    def test_gives_up_after_max_iterations_without_false_success(self, mock_chat, mock_execute):
        from models.tool_result import ToolResult

        mock_chat.return_value = LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="c", tool="git_status", arguments={})],
        )
        mock_execute.return_value = ToolResult(success=True, output="clean")

        agent = Agent()
        agent.run("keep checking status forever")

        self.assertEqual(mock_chat.call_count, 5)  # MAX_ITERATIONS in agent.py


if __name__ == "__main__":
    unittest.main()