import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "storage/logs/audit.jsonl")


def new_session_id() -> str:
    """One id per Agent.run() call, so every LLM call and tool execution
    within a single user request can be grouped together in the log."""
    return uuid.uuid4().hex[:12]


class AuditLogger:
    """
    Append-only, structured (JSON Lines) log of everything the agent
    does: every LLM call and every tool execution.

    This exists because terminal output disappears the moment a session
    ends — there was no way to answer "what did this agent actually do
    last week" or "was this destructive action confirmed by a human."
    This is the permanent, queryable record. It's also a prerequisite for
    an automated eval harness later: scoring the agent's behavior against
    a fixed set of tasks needs a record of what it actually did on each
    run, not just what printed to a terminal that's since been closed.

    One JSON object per line (not one big JSON array) so the log is
    grep-able, survives a crash mid-run without corrupting earlier
    entries, and can be tailed/streamed.
    """

    def __init__(self, path: str = DEFAULT_LOG_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, record: Dict[str, Any]) -> None:
        record = {"timestamp": time.time(), **record}
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def log_llm_call(
        self,
        session_id: str,
        iteration: int,
        model: str,
        tool_call_count: int,
        has_final_answer: bool,
        duration_ms: float,
    ) -> None:
        self._write({
            "event": "llm_call",
            "session_id": session_id,
            "iteration": iteration,
            "model": model,
            "tool_call_count": tool_call_count,
            "has_final_answer": has_final_answer,
            "duration_ms": round(duration_ms, 1),
        })

    def log_tool_call(
        self,
        session_id: str,
        tool: str,
        arguments: Dict[str, Any],
        sandboxed: bool,
        required_confirmation: bool,
        confirmed: Optional[bool],
        success: bool,
        error: Optional[str],
        duration_ms: float,
    ) -> None:
        self._write({
            "event": "tool_call",
            "session_id": session_id,
            "tool": tool,
            "arguments": arguments,
            "sandboxed": sandboxed,
            "required_confirmation": required_confirmation,
            "confirmed": confirmed,
            "success": success,
            "error": error,
            "duration_ms": round(duration_ms, 1),
        })