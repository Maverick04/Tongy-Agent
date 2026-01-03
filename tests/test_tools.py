"""
Tests for the tool system.
"""

import pytest
import tempfile
from pathlib import Path

from tongy_agent.tools.base import Tool
from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool, EditFileTool
from tongy_agent.tools.todo_tool import TodoWriteTool
from tongy_agent.schema.schema import ToolResult


class TestReadFileTool:
    """Tests for ReadFileTool."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def read_tool(self, temp_dir):
        """Create a read tool without sandbox."""
        return ReadFileTool(sandbox=None)

    def test_read_existing_file(self, read_tool, temp_dir):
        """Test reading an existing file."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        result = await read_tool.execute(path=str(test_file))

        assert result.success
        assert result.content == "Hello, World!"

    def test_read_nonexistent_file(self, read_tool):
        """Test reading a non-existent file."""
        result = await read_tool.execute(path="/nonexistent/file.txt")

        assert not result.success
        assert "not found" in result.error.lower()

    def test_read_with_offset_and_limit(self, read_tool, temp_dir):
        """Test reading with offset and limit."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\n")

        result = await read_tool.execute(path=str(test_file), offset=1, limit=2)

        assert result.success
        assert "Line 2" in result.content
        assert "Line 3" in result.content


class TestWriteFileTool:
    """Tests for WriteFileTool."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def write_tool(self):
        """Create a write tool without sandbox."""
        return WriteFileTool(sandbox=None)

    @pytest.mark.asyncio
    async def test_write_new_file(self, write_tool, temp_dir):
        """Test writing a new file."""
        test_file = Path(temp_dir) / "new.txt"

        result = await write_tool.execute(
            path=str(test_file),
            content="New content",
        )

        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "New content"

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self, write_tool, temp_dir):
        """Test overwriting an existing file."""
        test_file = Path(temp_dir) / "existing.txt"
        test_file.write_text("Old content")

        result = await write_tool.execute(
            path=str(test_file),
            content="New content",
        )

        assert result.success
        assert test_file.read_text() == "New content"


class TestEditFileTool:
    """Tests for EditFileTool."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def edit_tool(self):
        """Create an edit tool without sandbox."""
        return EditFileTool(sandbox=None)

    @pytest.mark.asyncio
    async def test_edit_file(self, edit_tool, temp_dir):
        """Test editing a file."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello World\nGoodbye World\n")

        result = await edit_tool.execute(
            path=str(test_file),
            old_string="Hello",
            new_string="Hi",
        )

        assert result.success
        assert "Hi World" in test_file.read_text()

    @pytest.mark.asyncio
    async def test_replace_all(self, edit_tool, temp_dir):
        """Test replace_all option."""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("cat cat cat\n")

        result = await edit_tool.execute(
            path=str(test_file),
            old_string="cat",
            new_string="dog",
            replace_all=True,
        )

        assert result.success
        assert test_file.read_text() == "dog dog dog\n"


class TestTodoWriteTool:
    """Tests for TodoWriteTool."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def todo_tool(self, temp_dir):
        """Create a TODO tool."""
        return TodoWriteTool(workspace_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_add_todos(self, todo_tool):
        """Test adding TODOs."""
        result = await todo_tool.execute(todos=[
            {
                "content": "Task 1",
                "status": "pending",
                "activeForm": "Working on Task 1",
            },
            {
                "content": "Task 2",
                "status": "pending",
                "activeForm": "Working on Task 2",
            },
        ])

        assert result.success
        assert "Task 1" in result.content

    @pytest.mark.asyncio
    async def test_update_todo_status(self, todo_tool):
        """Test updating TODO status."""
        # Add initial TODOs
        await todo_tool.execute(todos=[
            {
                "content": "Task 1",
                "status": "pending",
                "activeForm": "Working on Task 1",
            },
        ])

        # Update status
        result = await todo_tool.execute(todos=[
            {
                "content": "Task 1",
                "status": "completed",
                "activeForm": "Working on Task 1",
            },
        ])

        assert result.success
        assert "✅" in result.content

    @pytest.mark.asyncio
    async def test_only_one_in_progress(self, todo_tool):
        """Test that only one TODO can be in_progress."""
        result = await todo_tool.execute(todos=[
            {
                "content": "Task 1",
                "status": "in_progress",
                "activeForm": "Working on Task 1",
            },
            {
                "content": "Task 2",
                "status": "in_progress",
                "activeForm": "Working on Task 2",
            },
        ])

        assert not result.success
        assert "Only one todo" in result.error
