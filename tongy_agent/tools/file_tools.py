"""
File operation tools for Tongy-Agent.

Provides Read, Write, and Edit tools for file manipulation.
"""

import difflib
import os
from pathlib import Path
from typing import Any

from tongy_agent.schema.schema import ToolResult
from tongy_agent.tools.base import Tool


def _generate_unified_diff(
    old_text: str,
    new_text: str,
    filepath: str = "file",
    context_lines: int = 3
) -> str:
    """
    Generate a unified diff between two texts.

    Args:
        old_text: Original text
        new_text: Modified text
        filepath: File path for display in diff header
        context_lines: Number of context lines to show

    Returns:
        Unified diff string
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm="",
        n=context_lines
    )

    return "".join(diff)


class ReadFileTool(Tool):
    """Tool for reading file contents."""

    def __init__(self, sandbox: Any = None, workspace_dir: str = "./workspace"):
        """
        Initialize the ReadFile tool.

        Args:
            sandbox: Optional sandbox for access control
            workspace_dir: Workspace directory path
        """
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return """Read the contents of a file.

Use this tool when you need to read a file's contents. The file path must be within the allowed workspace.
Returns the file contents as a text string."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "Optional line number to start reading from (0-indexed)",
                    "default": 0,
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional maximum number of lines to read",
                    "default": 0,  # 0 means read all
                },
            },
            "required": ["path"],
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to workspace directory.

        Args:
            path: File path (can be absolute or relative)

        Returns:
            Resolved absolute path
        """
        path_obj = Path(path).expanduser()
        if path_obj.is_absolute():
            return path_obj
        return self.workspace_dir / path_obj

    async def execute(self, path: str, offset: int = 0, limit: int = 0) -> ToolResult:
        """Execute the file read operation."""
        try:
            # Resolve path relative to workspace
            file_path = self._resolve_path(path)

            # Sandbox check
            if self.sandbox:
                allowed, reason = self.sandbox.is_allowed(file_path)
                if not allowed:
                    return ToolResult(success=False, content="", error=reason)

                size_ok, size_reason = self.sandbox.check_file_size(file_path)
                if not size_ok:
                    return ToolResult(success=False, content="", error=size_reason)

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path is not a file: {path}",
                )

            # Read file contents
            with open(file_path, "r", encoding="utf-8") as f:
                if limit > 0:
                    # Read specific line range
                    lines = f.readlines()
                    content = "".join(lines[offset:offset + limit])
                else:
                    content = f.read()

            return ToolResult(success=True, content=content)

        except PermissionError:
            return ToolResult(
                success=False,
                content="",
                error=f"Permission denied: {path}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error reading file: {e}",
            )


class WriteFileTool(Tool):
    """Tool for writing to files."""

    def __init__(self, sandbox: Any = None, workspace_dir: str = "./workspace"):
        """
        Initialize the WriteFile tool.

        Args:
            sandbox: Optional sandbox for access control
            workspace_dir: Workspace directory path
        """
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return """Write content to a file.

Creates the file if it doesn't exist, overwrites if it does.
Use this tool to create new files or completely replace existing file contents.
Paths are relative to the workspace directory unless absolute."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write (relative to workspace unless absolute)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["path", "content"],
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to workspace directory.

        Args:
            path: File path (can be absolute or relative)

        Returns:
            Resolved absolute path
        """
        path_obj = Path(path).expanduser()
        if path_obj.is_absolute():
            return path_obj
        return self.workspace_dir / path_obj

    async def execute(self, path: str, content: str) -> ToolResult:
        """Execute the file write operation."""
        try:
            # Resolve path relative to workspace
            file_path = self._resolve_path(path)

            # Sandbox check
            if self.sandbox:
                allowed, reason = self.sandbox.is_allowed(file_path)
                if not allowed:
                    return ToolResult(success=False, content="", error=reason)

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                content=f"Successfully wrote {len(content)} characters to {path}",
            )

        except PermissionError:
            return ToolResult(
                success=False,
                content="",
                error=f"Permission denied: {path}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error writing file: {e}",
            )


class EditFileTool(Tool):
    """Tool for editing files with exact string replacement."""

    def __init__(self, sandbox: Any = None, workspace_dir: str = "./workspace"):
        """
        Initialize the EditFile tool.

        Args:
            sandbox: Optional sandbox for access control
            workspace_dir: Workspace directory path
        """
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return """Edit a file by replacing exact text.

Use this tool to make specific edits to existing files.
The old_string must match exactly (including whitespace).
Use replace_all=true to replace all occurrences.
Paths are relative to the workspace directory unless absolute."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit (relative to workspace unless absolute)",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "New text to insert",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default: false)",
                    "default": False,
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to workspace directory.

        Args:
            path: File path (can be absolute or relative)

        Returns:
            Resolved absolute path
        """
        path_obj = Path(path).expanduser()
        if path_obj.is_absolute():
            return path_obj
        return self.workspace_dir / path_obj

    async def execute(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> ToolResult:
        """Execute the file edit operation."""
        try:
            # Resolve path relative to workspace
            file_path = self._resolve_path(path)

            # Sandbox check
            if self.sandbox:
                allowed, reason = self.sandbox.is_allowed(file_path)
                if not allowed:
                    return ToolResult(success=False, content="", error=reason)

                size_ok, size_reason = self.sandbox.check_file_size(file_path)
                if not size_ok:
                    return ToolResult(success=False, content="", error=size_reason)

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"File not found: {path}",
                )

            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Perform replacement
            if old_string not in content:
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Old string not found in file: {old_string[:50]}...",
                )

            if replace_all:
                new_content = content.replace(old_string, new_string)
                count = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                count = 1

            # Write updated content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Generate unified diff
            diff_output = _generate_unified_diff(content, new_content, path)

            # Format the result message
            result_msg = f"Replaced {count} occurrence(s) in {path}"
            if diff_output:
                result_msg += f"\n\n---\n{diff_output}"

            return ToolResult(
                success=True,
                content=result_msg,
            )

        except PermissionError:
            return ToolResult(
                success=False,
                content="",
                error=f"Permission denied: {path}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error editing file: {e}",
            )


class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""

    def __init__(self, sandbox: Any = None, workspace_dir: str = "./workspace"):
        """
        Initialize the ListDirectory tool.

        Args:
            sandbox: Optional sandbox for access control
            workspace_dir: Workspace directory path
        """
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return """List the contents of a directory.

Returns a list of files and directories in the specified path.
Paths are relative to the workspace directory unless absolute."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list (relative to workspace unless absolute)",
                },
            },
            "required": ["path"],
        }

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to workspace directory.

        Args:
            path: Directory path (can be absolute or relative)

        Returns:
            Resolved absolute path
        """
        path_obj = Path(path).expanduser()
        if path_obj.is_absolute():
            return path_obj
        return self.workspace_dir / path_obj

    async def execute(self, path: str) -> ToolResult:
        """Execute the directory listing operation."""
        try:
            # Resolve path relative to workspace
            dir_path = self._resolve_path(path)

            # Sandbox check
            if self.sandbox:
                allowed, reason = self.sandbox.is_allowed(dir_path)
                if not allowed:
                    return ToolResult(success=False, content="", error=reason)

            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Directory not found: {path}",
                )

            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    content="",
                    error=f"Path is not a directory: {path}",
                )

            # List contents
            entries = []
            for entry in sorted(dir_path.iterdir()):
                entry_type = "DIR" if entry.is_dir() else "FILE"
                entries.append(f"{entry_type}: {entry.name}")

            content = "\n".join(entries) if entries else "(empty directory)"

            return ToolResult(success=True, content=content)

        except PermissionError:
            return ToolResult(
                success=False,
                content="",
                error=f"Permission denied: {path}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error listing directory: {e}",
            )
