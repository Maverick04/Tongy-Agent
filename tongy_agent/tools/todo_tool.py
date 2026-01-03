"""
TODO tool for Tongy-Agent.

Provides task tracking and management capabilities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from tongy_agent.schema.schema import ToolResult
from tongy_agent.tools.base import Tool


class TodoWriteTool(Tool):
    """Tool for managing TODO tasks."""

    def __init__(self, workspace_dir: str | None = None):
        """
        Initialize the TodoWrite tool.

        Args:
            workspace_dir: Directory to store TODO data
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.todo_file = self.workspace_dir / ".tongy_todos.json"
        self.todos = self._load_todos()

    def _load_todos(self) -> dict[str, Any]:
        """Load todos from file."""
        if self.todo_file.exists():
            try:
                data = json.loads(self.todo_file.read_text())
                return data.get("todos", [])
            except Exception:
                return []
        return []

    def _save_todos(self):
        """Save todos to file."""
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "todos": self.todos,
            "updated_at": datetime.now().isoformat(),
        }
        self.todo_file.write_text(json.dumps(data, indent=2))

    @property
    def name(self) -> str:
        return "TodoWrite"

    @property
    def description(self) -> str:
        return """Manage TODO tasks for the current session.

Use this tool to create, update, and track tasks during development.
Tasks have three states: pending, in_progress, and completed."""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Task description (imperative form)",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                                "description": "Current task status",
                            },
                            "activeForm": {
                                "type": "string",
                                "description": "Present continuous form of the task",
                            },
                        },
                        "required": ["content", "status", "activeForm"],
                    },
                    "description": "List of todos to manage",
                },
            },
            "required": ["todos"],
        }

    async def execute(self, todos: list[dict[str, Any]]) -> ToolResult:
        """Execute the TODO update operation."""
        try:
            # Update existing todos and add new ones
            existing_map = {todo.get("id"): todo for todo in self.todos if "id" in todo}

            updated_todos = []
            for todo_data in todos:
                # Generate ID if not present
                if "id" not in todo_data:
                    todo_data["id"] = str(uuid4())

                content = todo_data.get("content", "")
                status = todo_data.get("status", "pending")
                active_form = todo_data.get("activeForm", content)

                # Update existing or add new
                todo_id = todo_data["id"]
                if todo_id in existing_map:
                    existing = existing_map[todo_id]
                    existing.update({
                        "content": content,
                        "status": status,
                        "activeForm": active_form,
                        "updated_at": datetime.now().isoformat(),
                    })
                    updated_todos.append(existing)
                else:
                    new_todo = {
                        "id": todo_id,
                        "content": content,
                        "status": status,
                        "activeForm": active_form,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    }
                    updated_todos.append(new_todo)

            # Keep track of in_progress todo
            in_progress_count = sum(1 for t in updated_todos if t.get("status") == "in_progress")
            if in_progress_count > 1:
                return ToolResult(
                    success=False,
                    content="",
                    error="Only one todo can be in_progress at a time",
                )

            self.todos = updated_todos
            self._save_todos()

            # Generate summary
            summary_lines = ["## TODO List\n"]
            for todo in self.todos:
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                }.get(todo.get("status", "pending"), "❓")

                summary_lines.append(f"{status_emoji} {todo.get('content', '')}")

            content = "\n".join(summary_lines)
            return ToolResult(success=True, content=content)

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Error updating todos: {e}",
            )

    def get_todos(self) -> list[dict[str, Any]]:
        """Get current todos."""
        return self.todos.copy()

    def get_summary(self) -> str:
        """Get a summary of current todos."""
        if not self.todos:
            return "No tasks tracked"

        summary_lines = []
        for todo in self.todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
            }.get(status, "❓")
            summary_lines.append(f"{status_emoji} {content}")

        return "\n".join(summary_lines)
