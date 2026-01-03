"""
Tests for the memory system.
"""

import pytest
import tempfile
from pathlib import Path

from tongy_agent.memory import RepositoryMemory


class TestRepositoryMemory:
    """Tests for RepositoryMemory."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def memory(self, temp_repo):
        """Create a repository memory for testing."""
        return RepositoryMemory(temp_repo)

    def test_add_memory(self, memory):
        """Test adding a memory."""
        item = memory.add("test_key", "test_value", "test_category")

        assert item.key == "test_key"
        assert item.value == "test_value"
        assert item.category == "test_category"

    def test_get_memory(self, memory):
        """Test retrieving a memory."""
        memory.add("test_key", "test_value", "test_category")

        items = memory.get("test_key")
        assert len(items) == 1
        assert items[0].value == "test_value"

    def test_search_memory(self, memory):
        """Test searching memories."""
        memory.add("python_tip", "Use list comprehensions", "tips")
        memory.add("python_tip", "Use type hints", "tips")

        items = memory.search("python")
        assert len(items) >= 1

    def test_get_category(self, memory):
        """Test getting memories by category."""
        memory.add("key1", "value1", "category1")
        memory.add("key2", "value2", "category1")
        memory.add("key3", "value3", "category2")

        cat1_items = memory.get_category("category1")
        assert len(cat1_items) == 2

    def test_delete_memory(self, memory):
        """Test deleting a memory."""
        memory.add("test_key", "test_value", "test_category")

        deleted = memory.delete("test_key")
        assert deleted

        items = memory.get("test_key")
        assert len(items) == 0

    def test_get_context_prompt(self, memory):
        """Test getting context prompt."""
        memory.add("project_name", "Tongy-Agent", "general")
        memory.add("language", "Python", "general")

        prompt = memory.get_context_prompt()
        assert "Tongy-Agent" in prompt
        assert "Python" in prompt
