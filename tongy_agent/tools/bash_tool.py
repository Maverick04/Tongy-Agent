"""
Bash execution tool for Tongy-Agent.

Provides the ability to execute shell commands with safety controls.
"""

import os
import subprocess
from typing import Any

from tongy_agent.schema.schema import ToolResult
from tongy_agent.tools.base import Tool


class BashTool(Tool):
    """Tool for executing bash commands."""

    def __init__(self, sandbox: Any = None, cwd: str | None = None):
        """
        Initialize the Bash tool.

        Args:
            sandbox: Optional sandbox for command access control
            cwd: Current working directory for commands
        """
        self.sandbox = sandbox
        self.cwd = cwd

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """Execute a bash command in the terminal.

Use this tool to run shell commands, scripts, and system operations.
Commands run with the workspace as the current directory."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)",
                    "default": 120,
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str, timeout: int = 120) -> ToolResult:
        """Execute the bash command."""
        try:
            # Sandbox check
            if self.sandbox:
                # Extract command name (first word)
                cmd_name = command.split()[0] if command.split() else ""
                allowed, reason = self.sandbox.is_command_allowed(cmd_name)
                if not allowed:
                    return ToolResult(success=False, content="", error=reason)

            # Determine working directory
            cwd = self.cwd if self.cwd else os.getcwd()

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Command timed out after {timeout} seconds",
                )

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Combine stdout and stderr
            if stderr_str and process.returncode != 0:
                content = f"{stdout_str}\nError: {stderr_str}"
            else:
                content = stdout_str

            return ToolResult(
                success=process.returncode == 0,
                content=content,
                error=stderr_str if process.returncode != 0 else None,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error executing command: {e}",
            )


# Import asyncio for async operations
import asyncio
