import json
import unittest
from unittest.mock import MagicMock, patch

from llm.litellm_provider import LiteLLMProvider


def _fake_litellm_response(content=None, tool_calls=None):
    """Builds a minimal object shaped like litellm.completion()'s return
    value, just enough for LiteLLMProvider.chat() to read from."""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls or []

    response = MagicMock()
    response.choices = [MagicMock(message=message)]
    return response


class LiteLLMProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = LiteLLMProvider()

    @patch("llm.litellm_provider.litellm.completion")
    def test_plain_text_reply_has_no_tool_calls(self, mock_completion):
        mock_completion.return_value = _fake_litellm_response(content="Hello!")

        result = self.provider.chat(
            [{"role": "user", "content": "Say hello in one line"}]
        )

        self.assertEqual(result.content, "Hello!")
        self.assertEqual(result.tool_calls, [])

    @patch("llm.litellm_provider.litellm.completion")
    def test_tool_call_is_parsed_into_toolcall(self, mock_completion):
        raw_call = MagicMock()
        raw_call.id = "call_1"
        raw_call.function.name = "git_status"
        raw_call.function.arguments = json.dumps({})

        mock_completion.return_value = _fake_litellm_response(
            content=None, tool_calls=[raw_call]
        )

        result = self.provider.chat(
            [{"role": "user", "content": "what's my git status?"}],
            tools=[{"type": "function", "function": {"name": "git_status"}}],
        )

        self.assertIsNone(result.content)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].tool, "git_status")
        self.assertEqual(result.tool_calls[0].arguments, {})
        self.assertEqual(result.tool_calls[0].id, "call_1")

    @patch("llm.litellm_provider.litellm.completion")
    def test_malformed_tool_arguments_raise_clear_error(self, mock_completion):
        raw_call = MagicMock()
        raw_call.id = "call_1"
        raw_call.function.name = "git_push"
        raw_call.function.arguments = "{not valid json"

        mock_completion.return_value = _fake_litellm_response(
            content=None, tool_calls=[raw_call]
        )

        with self.assertRaises(ValueError):
            self.provider.chat([{"role": "user", "content": "push my branch"}])


if __name__ == "__main__":
    unittest.main()