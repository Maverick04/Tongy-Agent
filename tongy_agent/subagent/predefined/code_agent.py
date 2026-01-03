"""
Predefined sub-agents for common tasks.

This module provides ready-to-use sub-agents for specific domains.
"""

from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.subagent.base import SubAgent


def create_code_subagent(
    llm_client: GLMClient,
    tools: list,
    workspace_dir: str = "./workspace",
) -> SubAgent:
    """
    Create a code-focused sub-agent.

    Args:
        llm_client: LLM client
        tools: Available tools
        workspace_dir: Workspace directory

    Returns:
        Configured code sub-agent
    """
    system_prompt = """# Code Assistant

You are a specialized code assistant focused on:
- Reading and analyzing code
- Writing new code and features
- Debugging and fixing issues
- Refactoring and optimization
- Code review and best practices

Always provide clean, well-documented code following best practices.
"""

    return SubAgent(
        name="code",
        description="Specialized assistant for code-related tasks including writing, analyzing, and debugging code",
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=30,
    )


def create_research_subagent(
    llm_client: GLMClient,
    tools: list,
    workspace_dir: str = "./workspace",
) -> SubAgent:
    """
    Create a research-focused sub-agent.

    Args:
        llm_client: LLM client
        tools: Available tools
        workspace_dir: Workspace directory

    Returns:
        Configured research sub-agent
    """
    system_prompt = """# Research Assistant

You are a specialized research assistant focused on:
- Finding and analyzing information
- Reading documentation
- Exploring codebases
- Summarizing findings
- Providing context and background

Be thorough and cite your sources when possible.
"""

    return SubAgent(
        name="research",
        description="Specialized assistant for research tasks including exploring codebases, reading documentation, and gathering information",
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=20,
    )


def create_testing_subagent(
    llm_client: GLMClient,
    tools: list,
    workspace_dir: str = "./workspace",
) -> SubAgent:
    """
    Create a testing-focused sub-agent.

    Args:
        llm_client: LLM client
        tools: Available tools
        workspace_dir: Workspace directory

    Returns:
        Configured testing sub-agent
    """
    system_prompt = """# Testing Assistant

You are a specialized testing assistant focused on:
- Writing unit tests
- Creating integration tests
- Test coverage analysis
- Debugging test failures
- Suggesting test improvements

Focus on writing clear, maintainable tests that cover edge cases.
"""

    return SubAgent(
        name="testing",
        description="Specialized assistant for testing tasks including writing tests, analyzing coverage, and debugging test failures",
        llm_client=llm_client,
        system_prompt=system_prompt,
        tools=tools,
        workspace_dir=workspace_dir,
        max_steps=25,
    )
