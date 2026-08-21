import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables
load_dotenv()


class LLMConfig(BaseModel):
    provider: str = Field(..., description="Default LLM provider")
    model: str = Field(..., description="Model name")

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None


class AppConfig(BaseModel):
    llm: LLMConfig
    log_level: str = "INFO"


def load_config() -> AppConfig:
    """
    Loads configuration from environment variables
    and returns a strongly-typed config object.
    """

    llm_config = LLMConfig(
        provider=os.getenv("DEFAULT_PROVIDER", "openai"),
        model=os.getenv("MODEL", "gpt-5-mini"),

        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    config = AppConfig(
        llm=llm_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    return config


# Singleton config instance (import this everywhere)
config = load_config()