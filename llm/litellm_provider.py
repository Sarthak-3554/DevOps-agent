import json
import os
from typing import Any, Dict, List, Optional

import litellm
from dotenv import load_dotenv

from llm.base import BaseLLM
from models.llm_response import LLMResponse
from models.tool_call import ToolCall

load_dotenv(override=True)

# Different providers/models accept different subsets of OpenAI-style
# params (e.g. GPT-5 models reject any temperature other than 1). Rather
# than hardcoding per-model exceptions here, let litellm silently drop
# params a given model doesn't support instead of raising. This is what
# actually makes the provider-agnostic promise ("just change MODEL") hold
# in practice.
litellm.drop_params = True


class LiteLLMProvider(BaseLLM):
    """
    Provider-agnostic LLM client using litellm's native tool-calling.

    litellm normalizes the function-calling format across OpenAI,
    Anthropic, Groq, OpenRouter, etc., so switching providers is just
    changing the MODEL env var (e.g. "openai/gpt-4o-mini",
    "groq/llama-3.3-70b-versatile", "anthropic/claude-sonnet-4-6") —
    no per-provider parsing code needed.
    """

    def __init__(self):
        self.model = os.getenv("MODEL", "openai/gpt-4o-mini")
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None,
                temperature=self.temperature,
                max_tokens=1024,
            )
        except Exception as e:
            raise Exception(f"Provider error: {str(e)}") from e

        message = response.choices[0].message

        tool_calls: List[ToolCall] = []
        for raw_call in (message.tool_calls or []):
            try:
                arguments = json.loads(raw_call.function.arguments or "{}")
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Model returned invalid JSON arguments for "
                    f"'{raw_call.function.name}': {raw_call.function.arguments}"
                ) from e

            tool_calls.append(
                ToolCall(
                    id=raw_call.id,
                    tool=raw_call.function.name,
                    arguments=arguments,
                )
            )

        return LLMResponse(content=message.content, tool_calls=tool_calls)