from typing import List, Optional

from pydantic import BaseModel

from models.tool_call import ToolCall


class LLMResponse(BaseModel):
    """
    Normalized response from any LLM provider.

    - content: plain-text reply (used when the model isn't calling a tool,
      e.g. asking a clarifying question, or a final summary).
    - tool_calls: structured tool calls the model wants executed, parsed
      from the provider's native function-calling response (not from
      regex-stripped JSON in the message text).
    """

    content: Optional[str] = None
    tool_calls: List[ToolCall] = []
