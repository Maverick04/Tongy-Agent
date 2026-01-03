"""
Base class for all tools.

Provides a common interface that all tool implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any

from tongy_agent.schema.schema import ToolResult


class Tool(ABC):
    """
    Abstract base class for tools.

    All tools must inherit from this class and implement the required methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        Return the JSON schema for the tool's parameters.

        This should follow the JSON Schema format for function calling.
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult containing the execution result
        """
        pass

    def to_schema(self) -> dict[str, Any]:
        """
        Convert the tool to a function calling schema.

        Returns:
            Dictionary representing the tool in function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self) -> str:
        return f"Tool(name={self.name})"
