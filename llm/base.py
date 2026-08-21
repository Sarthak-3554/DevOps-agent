from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from models.llm_response import LLMResponse


class BaseLLM(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        messages: OpenAI-style chat messages, including any prior
                  assistant tool_calls and "tool" role result messages.
        tools:    OpenAI-style tool/function schemas (see tools/registry.py
                  TOOL_SCHEMAS). Pass None for a plain text-only turn.
        returns:  LLMResponse(content=..., tool_calls=[ToolCall, ...])
                  — structured, not a raw string to be regex-parsed.
        """
        pass
