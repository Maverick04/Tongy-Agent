"""
SubAgent manager for Tongy-Agent.

Manages registration and delegation to sub-agents.
"""

import logging
from typing import Any

from tongy_agent.schema.schema import Tool, ToolResult
from tongy_agent.subagent.base import SubAgent

logger = logging.getLogger(__name__)


class DelegationTool(Tool):
    """Tool for delegating tasks to a sub-agent."""

    def __init__(self, subagent: SubAgent):
        """
        Initialize the delegation tool.

        Args:
            subagent: The sub-agent to delegate to
        """
        self.subagent = subagent

    @property
    def name(self) -> str:
        return f"delegate_to_{self.subagent.name}"

    @property
    def description(self) -> str:
        return self.subagent.description

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task to delegate to this sub-agent",
                },
            },
            "required": ["task"],
        }

    async def execute(self, task: str) -> ToolResult:
        """Execute the delegated task."""
        try:
            result = await self.subagent.execute(task)
            return ToolResult(success=True, content=result)
        except Exception as e:
            logger.error(f"SubAgent {self.subagent.name} failed: {e}")
            return ToolResult(
                success=False,
                content="",
                error=str(e),
            )


class SubAgentManager:
    """
    Manager for sub-agents.

    Handles registration, lookup, and delegation to sub-agents.
    """

    def __init__(self):
        """Initialize the sub-agent manager."""
        self.subagents: dict[str, SubAgent] = {}
        self.delegation_tools: dict[str, DelegationTool] = {}

    def register(self, subagent: SubAgent) -> bool:
        """
        Register a sub-agent.

        Args:
            subagent: Sub-agent to register

        Returns:
            True if registered successfully
        """
        if subagent.name in self.subagents:
            logger.warning(f"SubAgent {subagent.name} already registered, overwriting")

        self.subagents[subagent.name] = subagent
        self.delegation_tools[subagent.name] = DelegationTool(subagent)

        logger.info(f"Registered SubAgent: {subagent.name}")
        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister a sub-agent.

        Args:
            name: Name of sub-agent to unregister

        Returns:
            True if unregistered successfully
        """
        if name not in self.subagents:
            logger.warning(f"SubAgent {name} not registered")
            return False

        del self.subagents[name]
        del self.delegation_tools[name]

        logger.info(f"Unregistered SubAgent: {name}")
        return True

    def get(self, name: str) -> SubAgent | None:
        """
        Get a registered sub-agent.

        Args:
            name: Name of sub-agent

        Returns:
            SubAgent or None if not found
        """
        return self.subagents.get(name)

    def list_agents(self) -> list[dict[str, str]]:
        """
        List all registered sub-agents.

        Returns:
            List of agent descriptions
        """
        return [
            {"name": name, "description": agent.description}
            for name, agent in self.subagents.items()
        ]

    def get_delegation_tools(self) -> list[DelegationTool]:
        """
        Get delegation tools for all sub-agents.

        Returns:
            List of delegation tools
        """
        return list(self.delegation_tools.values())

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """
        Get tool schemas for all sub-agents.

        Returns:
            List of tool schemas
        """
        return [tool.to_schema() for tool in self.delegation_tools.values()]

    async def delegate(self, name: str, task: str) -> str:
        """
        Delegate a task to a sub-agent.

        Args:
            name: Name of sub-agent
            task: Task to delegate

        Returns:
            Task result

        Raises:
            ValueError: If sub-agent not found
        """
        subagent = self.get(name)
        if not subagent:
            raise ValueError(f"SubAgent not found: {name}")

        return await subagent.execute(task)
