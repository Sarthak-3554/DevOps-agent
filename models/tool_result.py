from pydantic import BaseModel
from typing import Optional


class ToolResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None

    def __str__(self):
        if self.success:
            return f"[SUCCESS] {self.output}"
        return f"[ERROR] {self.error}"