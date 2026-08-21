import json

from agent.executor import Executor
from llm.factory import get_llm
from prompts import SYSTEM_PROMPT
from tools.registry import TOOL_SCHEMAS


class Agent:
    def __init__(self):
        self.llm = get_llm()

    def run(self, user_input: str):
        MAX_ITERATIONS = 5
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        for iteration in range(MAX_ITERATIONS):
            print(f"\n🧠 Iteration {iteration + 1}")

            response = self.llm.chat(messages, tools=TOOL_SCHEMAS)

            if not response.tool_calls:
                # Model responded in plain text: a clarifying question
                # (per the "ask instead of guessing" prompt rule), or a
                # final summary once the task is done.
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

            all_success = True

            # A single turn can contain multiple tool calls now that the
            # model isn't hand-writing a "plan" list — run each and report
            # its result back individually, matched by tool_call_id.
            for call in response.tool_calls:
                print(f"\n🚀 Executing: {call.tool} {call.arguments}")

                result = Executor.execute(call)
                print("RESULT:", result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                })

                if not result.success:
                    all_success = False

            if all_success:
                print("\n✅ Task completed successfully!")
                return

            print("\n🔁 Failure detected. Asking LLM to fix...")

        print("\n❌ Max iterations reached. Could not complete task.")
