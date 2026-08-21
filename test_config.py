import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # Load environment variables from .env file
client = OpenAI(
    base_url="https://sarthakdumbre09--ep-kimi-k3-server.us-west.modal.direct/v1",
    api_key=f"{os.environ['MODAL_PROXY_TOKEN_ID']}.{os.environ['MODAL_PROXY_TOKEN_SECRET']}",
)

completion = client.chat.completions.create(
    model="moonshotai/Kimi-K3",
    messages=[
        {
            "role": "system",
            "content": "You are a concise technical assistant.",
        },
        {
            "role": "user",
            "content": "Give me a command to push a new branch to a remote git repository.",
        },
    ],
    temperature=0.3,
    max_tokens=2048,
    top_p=0.95,
    stream=False,
    extra_body={"reasoning_effort": "none"},
)
print(completion.choices[0].message.content)