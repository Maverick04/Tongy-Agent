"""
Basic usage example for Tongy-Agent.

This example demonstrates the simplest way to use Tongy-Agent.
"""

import asyncio
import os

from tongy_agent.agent import Agent
from tongy_agent.config import ConfigManager
from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.memory import RepositoryMemory
from tongy_agent.sandbox import Sandbox
from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool
from tongy_agent.tools.bash_tool import BashTool


async def main():
    """Run a basic Tongy-Agent example."""

    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.config

    # Override API key from environment if needed
    api_key = os.getenv("TONGY_API_KEY", config.llm.api_key)
    if not api_key:
        print("Error: TONGY_API_KEY environment variable not set")
        print("Get your API key from: https://open.bigmodel.cn/")
        return

    # Initialize LLM client
    llm_client = GLMClient(
        api_key=api_key,
        model="glm-4.7",
    )

    # Initialize sandbox for security
    sandbox = Sandbox(config.sandbox)
    sandbox.configure_from_workspace("./workspace")

    # Initialize memory
    memory = RepositoryMemory("./workspace")

    # Create tools
    tools = [
        ReadFileTool(sandbox=sandbox),
        WriteFileTool(sandbox=sandbox),
        BashTool(sandbox=sandbox),
    ]

    # Load system prompt
    system_prompt = config_manager.get_system_prompt()

    # Create agent
    agent = Agent(
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir="./workspace",
        memory=memory,
        sandbox=sandbox,
    )

    # Example: Ask the agent to create a simple Python script
    user_request = """
    Create a simple Python script that calculates the Fibonacci sequence.
    The script should:
    - Be named fibonacci.py
    - Take a number as command line argument
    - Print the Fibonacci sequence up to that number
    - Include proper error handling
    """

    print(f"User request: {user_request}\n")

    # Add user message
    agent.add_user_message(user_request)

    # Run the agent
    print("Running agent...\n")
    response = await agent.run()

    print(f"\nAgent response:\n{response}")

    # Print conversation summary
    print(f"\n{agent.get_conversation_summary()}")

    # Close the LLM client
    await llm_client.close()


if __name__ == "__main__":
    asyncio.run(main())
