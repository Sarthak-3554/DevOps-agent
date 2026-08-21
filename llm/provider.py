import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from llm.base import BaseLLM

load_dotenv(dotenv_path=".env", override=True)


class Provider(BaseLLM):
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("GROQ_BASE_URL"),
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = os.getenv("MODEL_NAME", "llama3-70b-8192")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Provider error: {str(e)}")
