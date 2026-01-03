"""
Tools demonstration for Tongy-Agent.

Shows how to work with various tools.
"""

import asyncio
import os
import tempfile
from pathlib import Path

from tongy_agent.agent import Agent
from tongy_agent.config import ConfigManager
from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.sandbox import Sandbox
from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool
from tongy_agent.tools.bash_tool import BashTool
from tongy_agent.tools.todo_tool import TodoWriteTool


async def demo_file_tools():
    """Demonstrate file operation tools."""
    print("=== File Tools Demo ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create tools without sandbox for demo
        write_tool = WriteFileTool(sandbox=None)
        read_tool = ReadFileTool(sandbox=None)
        edit_tool = EditFileTool(sandbox=None)
        list_tool = ListDirectoryTool(sandbox=None)

        # Write a file
        test_file = Path(tmpdir) / "demo.txt"
        print(f"1. Writing to {test_file.name}")
        result = await write_tool.execute(
            path=str(test_file),
            content="Hello from Tongy-Agent!\nThis is a demo file."
        )
        print(f"   Result: {result.content}\n")

        # Read the file
        print(f"2. Reading {test_file.name}")
        result = await read_tool.execute(path=str(test_file))
        print(f"   Content:\n{result.content}\n")

        # Edit the file
        print(f"3. Editing {test_file.name}")
        result = await edit_tool.execute(
            path=str(test_file),
            old_string="Hello",
            new_string="Greetings"
        )
        print(f"   Result: {result.content}\n")

        # Read again to verify
        print(f"4. Reading {test_file.name} after edit")
        result = await read_tool.execute(path=str(test_file))
        print(f"   Content:\n{result.content}\n")

        # List directory
        print(f"5. Listing directory")
        result = await list_tool.execute(path=tmpdir)
        print(f"   Contents:\n{result.content}\n")


async def demo_bash_tool():
    """Demonstrate bash tool."""
    print("=== Bash Tool Demo ===\n")

    bash_tool = BashTool(sandbox=None)

    # Simple command
    print("1. Running: echo 'Hello from Bash!'")
    result = await bash_tool.execute(command="echo 'Hello from Bash!'")
    print(f"   Output: {result.content}\n")

    # List files
    print("2. Running: ls -la")
    result = await bash_tool.execute(command="ls -la | head -5")
    print(f"   Output: {result.content}\n")


async def demo_todo_tool():
    """Demonstrate TODO tool."""
    print("=== TODO Tool Demo ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        todo_tool = TodoWriteTool(workspace_dir=tmpdir)

        # Add TODOs
        print("1. Creating TODO list")
        result = await todo_tool.execute(todos=[
            {
                "content": "Learn Tongy-Agent",
                "status": "pending",
                "activeForm": "Learning Tongy-Agent",
            },
            {
                "content": "Build an AI assistant",
                "status": "in_progress",
                "activeForm": "Building an AI assistant",
            },
            {
                "content": "Deploy to production",
                "status": "pending",
                "activeForm": "Deploying to production",
            },
        ])
        print(f"   Result:\n{result.content}\n")

        # Update a TODO
        print("2. Marking task as completed")
        result = await todo_tool.execute(todos=[
            {
                "content": "Learn Tongy-Agent",
                "status": "completed",
                "activeForm": "Learning Tongy-Agent",
            },
            {
                "content": "Build an AI assistant",
                "status": "in_progress",
                "activeForm": "Building an AI assistant",
            },
            {
                "content": "Deploy to production",
                "status": "pending",
                "activeForm": "Deploying to production",
            },
        ])
        print(f"   Result:\n{result.content}\n")


async def demo_sandbox():
    """Demonstrate sandbox security."""
    print("=== Sandbox Demo ===\n")

    from tongy_agent.sandbox import FileSandbox, CommandSandbox, Sandbox
    from tongy_agent.schema.schema import SandboxConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        # Configure sandbox
        config = SandboxConfig(
            allowed_paths=[tmpdir],
            forbidden_commands=["rm", "dd"],
        )
        sandbox = Sandbox(config)

        # Test file access
        print("1. Testing file access control")

        allowed_file = Path(tmpdir) / "allowed.txt"
        allowed, reason = sandbox.is_file_allowed(allowed_file)
        print(f"   Allowed path: {allowed_file}")
        print(f"   Access: {allowed}\n")

        forbidden_path = "/etc/passwd"
        allowed, reason = sandbox.is_file_allowed(forbidden_path)
        print(f"   Forbidden path: {forbidden_path}")
        print(f"   Access: {allowed}")
        print(f"   Reason: {reason}\n")

        # Test command filtering
        print("2. Testing command filtering")

        safe_cmd = "ls -la"
        allowed, reason = sandbox.is_command_allowed(safe_cmd)
        print(f"   Safe command: {safe_cmd}")
        print(f"   Allowed: {allowed}\n")

        dangerous_cmd = "rm -rf /"
        allowed, reason = sandbox.is_command_allowed(dangerous_cmd)
        print(f"   Dangerous command: {dangerous_cmd}")
        print(f"   Allowed: {allowed}")
        print(f"   Reason: {reason}\n")


async def main():
    """Run all demos."""
    print("Tongy-Agent Tools Demonstration\n")
    print("=" * 50)

    await demo_file_tools()
    print("\n")
    await demo_bash_tool()
    print("\n")
    await demo_todo_tool()
    print("\n")
    await demo_sandbox()

    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
