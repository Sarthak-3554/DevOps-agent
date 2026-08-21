from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from pydantic import BaseModel

from models.tool_result import ToolResult


class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]  # pydantic model describing this tool's arguments

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        pass

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """
        OpenAI/litellm-style tool schema, generated from args_schema.

        This is the single source of truth for a tool's parameters: the
        pydantic model defines them once, and both validation (via
        args_schema(**kwargs)) and the LLM-facing schema (this method)
        derive from it. Nothing is hand-duplicated in prompts.py anymore.
        """
        parameters = cls.args_schema.model_json_schema()
        parameters.pop("title", None)
        for prop in parameters.get("properties", {}).values():
            prop.pop("title", None)

        # Explicitly forbid extra/hallucinated arguments. Without this,
        # a model can pass fields that don't exist on the tool (e.g.
        # git_status(branch=None)) and the schema won't stop it — the
        # call only fails later, inside Executor, wasting a retry
        # round-trip. Some providers (OpenAI/Groq-compatible strict mode)
        # will reject the malformed call before it even reaches our code.
        parameters["additionalProperties"] = False

        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": parameters,
            },
        }