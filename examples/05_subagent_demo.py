"""
SubAgent demonstration for Tongy-Agent.

Shows how to create and use SubAgents for task delegation.
"""

import asyncio
import os

from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.sandbox import Sandbox
from tongy_agent.schema.schema import SandboxConfig
from tongy_agent.subagent.base import SubAgent
from tongy_agent.subagent.manager import SubAgentManager
from tongy_agent.subagent.predefined import create_code_subagent, create_research_subagent
from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool
from tongy_agent.tools.bash_tool import BashTool


async def demo_basic_subagent():
    """Demonstrate basic SubAgent usage."""
    print("=== Basic SubAgent Demo ===\n")

    api_key = os.getenv("TONGY_API_KEY")
    if not api_key:
        print("Error: TONGY_API_KEY not set")
        return

    # Initialize LLM client
    llm = GLMClient(api_key=api_key)

    # Create tools
    sandbox = Sandbox(SandboxConfig())
    tools = [
        ReadFileTool(sandbox=sandbox),
        WriteFileTool(sandbox=sandbox),
        BashTool(sandbox=sandbox),
    ]

    # Create a custom SubAgent
    code_agent = SubAgent(
        name="python_expert",
        description="Expert in Python programming and best practices",
        llm_client=llm,
        system_prompt="""You are a Python programming expert.

You specialize in:
- Writing clean, idiomatic Python code
- Following PEP 8 guidelines
- Using type hints
- Writing docstrings
- Testing and debugging

Always provide well-documented, production-ready code.""",
        tools=tools,
        workspace_dir="./workspace",
    )

    # Use the SubAgent
    task = "Write a Python function that validates email addresses using regex"
    print(f"Task: {task}\n")

    result = await code_agent.execute(task)
    print(f"Result:\n{result}\n")

    await llm.close()


async def demo_predefined_subagents():
    """Demonstrate predefined SubAgents."""
    print("=== Predefined SubAgents Demo ===\n")

    api_key = os.getenv("TONGY_API_KEY")
    if not api_key:
        print("Error: TONGY_API_KEY not set")
        return

    # Initialize LLM client
    llm = GLMClient(api_key=api_key)

    # Create tools
    sandbox = Sandbox(SandboxConfig())
    tools = [ReadFileTool(sandbox=sandbox), WriteFileTool(sandbox=sandbox)]

    # Create predefined SubAgents
    code_agent = create_code_subagent(llm, tools)
    research_agent = create_research_subagent(llm, tools)

    print("Available SubAgents:")
    print(f"  - {code_agent.name}: {code_agent.description}")
    print(f"  - {research_agent.name}: {research_agent.description}\n")

    # Use code agent
    print("Using code agent...")
    result = await code_agent.execute("Create a simple FastAPI endpoint")
    print(f"Code agent result:\n{result}\n")

    # Use research agent
    print("Using research agent...")
    result = await research_agent.execute("Find information about async/await in Python")
    print(f"Research agent result:\n{result}\n")

    await llm.close()


async def demo_subagent_manager():
    """Demonstrate SubAgent manager."""
    print("=== SubAgent Manager Demo ===\n")

    api_key = os.getenv("TONGY_API_KEY")
    if not api_key:
        print("Error: TONGY_API_KEY not set")
        return

    # Initialize
    llm = GLMClient(api_key=api_key)
    sandbox = Sandbox(SandboxConfig())
    tools = [ReadFileTool(sandbox=sandbox)]

    # Create manager
    manager = SubAgentManager()

    # Create and register SubAgents
    code_agent = SubAgent(
        name="code",
        description="Handles coding tasks",
        llm_client=llm,
        system_prompt="You are a coding assistant.",
        tools=tools,
        workspace_dir="./workspace",
    )

    test_agent = SubAgent(
        name="testing",
        description="Handles testing tasks",
        llm_client=llm,
        system_prompt="You are a testing assistant.",
        tools=tools,
        workspace_dir="./workspace",
    )

    manager.register(code_agent)
    manager.register(test_agent)

    # List registered agents
    print("Registered SubAgents:")
    for agent_info in manager.list_agents():
        print(f"  - {agent_info['name']}: {agent_info['description']}\n")

    # Get delegation tools
    delegation_tools = manager.get_delegation_tools()
    print(f"Delegation tools: {len(delegation_tools)}\n")

    # Delegate tasks
    print("Delegating to code agent...")
    result = await manager.delegate("code", "Write a hello world function")
    print(f"Result: {result[:100]}...\n")

    await llm.close()


async def main():
    """Run all demos."""
    print("Tongy-Agent SubAgent Demonstration\n")
    print("=" * 50)

    # Note: These demos require a valid API key
    print("Note: These demos require TONGY_API_KEY to be set\n")

    await demo_basic_subagent()
    print("\n")
    await demo_predefined_subagents()
    print("\n")
    await demo_subagent_manager()

    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
