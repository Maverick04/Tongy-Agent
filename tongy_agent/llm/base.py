"""
Base class for LLM clients.

Provides a common interface that all LLM client implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any

from tongy_agent.schema.schema import LLMResponse, Message, RetryConfig


class LLMClientBase(ABC):
    """
    Abstract base class for LLM clients.

    All LLM client implementations must inherit from this class and implement
    the generate method.
    """

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        retry_config: RetryConfig | None = None,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: API key for authentication
            api_base: Base URL for the API
            model: Model name to use
            retry_config: Retry configuration (optional)
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.retry_config = retry_config or RetryConfig()

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[Any] | None = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of messages in the conversation
            tools: List of available tools (for function calling)

        Returns:
            LLMResponse containing the generated content and tool calls

        Raises:
            Exception: If the API call fails after retries
        """
        pass

    def _convert_tools_to_schema(self, tools: list[Any]) -> list[dict[str, Any]]:
        """
        Convert tool objects to API-compatible schema.

        Args:
            tools: List of tool objects

        Returns:
            List of tool schemas
        """
        if not tools:
            return []

        tool_schemas = []
        for tool in tools:
            if hasattr(tool, "to_schema"):
                tool_schemas.append(tool.to_schema())
            else:
                # Assume tool has name, description, parameters attributes
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                tool_schemas.append(schema)

        return tool_schemas

    def estimate_tokens(self, messages: list[Message]) -> int:
        """
        Estimate the number of tokens in a list of messages.

        This is a rough estimate. For accurate counting, use tiktoken.

        Args:
            messages: List of messages

        Returns:
            Estimated token count
        """
        total = 0
        for msg in messages:
            content = msg.content
            if isinstance(content, str):
                # Rough estimate: 1 token ≈ 4 characters for English
                # For Chinese, 1 token ≈ 1.5-2 characters
                total += len(content) // 3
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if "text" in item:
                            total += len(item["text"]) // 3
                        elif "image_url" in item:
                            # Images are typically ~1000 tokens
                            total += 1000

        return total
