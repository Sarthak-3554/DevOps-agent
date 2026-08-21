from typing import Any, Dict, Optional

from pydantic import BaseModel


class ToolCall(BaseModel):
    # Provider-assigned id for this specific call (e.g. "call_abc123").
    # Required to send the tool's result back as a matching "tool" role
    # message in multi-turn function-calling conversations. Optional here
    # so ToolCall can still be constructed manually (tests, internal use).
    id: Optional[str] = None
    tool: str
    arguments: Dict[str, Any]

    def __str__(self):
        return f"ToolCall(tool={self.tool}, args={self.arguments})"
