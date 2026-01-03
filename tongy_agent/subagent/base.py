"""
SubAgent base class for Tongy-Agent.

Provides a foundation for creating specialized sub-agents.
"""

from typing import Any

from tongy_agent.agent import Agent


class SubAgent(Agent):
    """
    Base class for sub-agents.

    Sub-agents are specialized agents that can be delegated specific tasks.
    They inherit from Agent but add metadata and capabilities for delegation.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parent_agent: Agent | None = None,
        **kwargs,
    ):
        """
        Initialize the SubAgent.

        Args:
            name: Unique name for this sub-agent
            description: Description of what this sub-agent does
            parent_agent: Optional parent agent that created this sub-agent
            **kwargs: Additional arguments passed to Agent
        """
        self.name = name
        self.description = description
        self.parent_agent = parent_agent

        # Call parent constructor
        super().__init__(**kwargs)

    async def execute(self, task: str) -> str:
        """
        Execute a delegated task.

        Args:
            task: Task description

        Returns:
            Task result
        """
        self.add_user_message(task)
        return await self.run()

    def to_tool_description(self) -> dict[str, Any]:
        """
        Convert this sub-agent to a tool description.

        Returns:
            Tool schema for delegation
        """
        return {
            "type": "function",
            "function": {
                "name": f"delegate_to_{self.name}",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Task to delegate to this sub-agent",
                        },
                    },
                    "required": ["task"],
                },
            },
        }
