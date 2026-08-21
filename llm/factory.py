from llm.base import BaseLLM
from llm.litellm_provider import LiteLLMProvider


def get_llm() -> BaseLLM:
    # litellm handles routing to OpenAI/Anthropic/Groq/OpenRouter/etc.
    # based on the MODEL env var prefix, so one provider class covers all
    # of them. Add a branch here only if you need a provider litellm
    # doesn't support directly.
    return LiteLLMProvider()
