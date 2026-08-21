import json
import time

from agent.executor import Executor
from agent.logger import AuditLogger, new_session_id
from llm.factory import get_llm
from prompts import SYSTEM_PROMPT
from tools.registry import TOOL_SCHEMAS

# Tool output fed back to the model is capped at this many characters.
# Some commands (apt-get, npm install, pip install) print hundreds of
# lines the model doesn't need to see in full to know whether the step
# succeeded — and left uncapped, a single verbose command can blow past
# a provider's per-request token limit on the very next turn (this is
# exactly what happened: an apt-get install's full log pushed a later
# request over Groq's 8k TPM limit). The model only needs enough to
# judge success/failure and react to real error messages.
MAX_TOOL_RESULT_CHARS = 3000


def _truncate_for_model(text: str) -> str:
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text

    omitted = len(text) - MAX_TOOL_RESULT_CHARS
    return (
        text[:MAX_TOOL_RESULT_CHARS]
        + f"\n... [output truncated, {omitted} more characters omitted]"
    )


class Agent:
    def __init__(self):
        self.llm = get_llm()
        self.logger = AuditLogger()

    def run(self, user_input: str):
        MAX_ITERATIONS = 5
        session_id = new_session_id()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        for iteration in range(MAX_ITERATIONS):
            print(f"\n🧠 Iteration {iteration + 1}")

            start = time.monotonic()
            response = self.llm.chat(messages, tools=TOOL_SCHEMAS)
            duration_ms = (time.monotonic() - start) * 1000

            self.logger.log_llm_call(
                session_id=session_id,
                iteration=iteration + 1,
                model=getattr(self.llm, "model", "unknown"),
                tool_call_count=len(response.tool_calls),
                has_final_answer=not response.tool_calls,
                duration_ms=duration_ms,
            )

            if not response.tool_calls:
                # This is the ONLY signal we trust for "the task is done":
                # the model itself responding in plain text with no more
                # tool calls. We deliberately do NOT infer completion from
                # "the last batch of tool calls succeeded" — a successful
                # tool call can be a remedial step (e.g. installing a
                # missing dependency) rather than the actual request, and
                # declaring victory there is a false success.
                print("\n💬", response.content)
                return

            # Record the assistant's turn, including the raw tool_calls,
            # so the "tool" result messages below have a matching call to
            # attach to (required by the OpenAI-style function-calling
            # message format that litellm normalizes providers to).
            messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.tool,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in response.tool_calls
                ],
            })

            # A single turn can contain multiple tool calls — run each and
            # report its result back individually, matched by tool_call_id.
            for call in response.tool_calls:
                print(f"\n🚀 Executing: {call.tool} {call.arguments}")

                result = Executor.execute(call, logger=self.logger, session_id=session_id)
                print("RESULT:", result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": _truncate_for_model(str(result)),
                })

            # Always hand control back to the model with the tool results
            # now in context. It decides — by calling another tool or by
            # responding in plain text — whether the original request has
            # actually been fulfilled. The harness never guesses.

        print("\n❌ Max iterations reached. Could not complete task.")