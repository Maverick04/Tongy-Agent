"""
Repository-level memory system for Tongy-Agent.

Provides persistent memory storage scoped to a repository/project.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from tongy_agent.schema.schema import MemoryItem

logger = logging.getLogger(__name__)


class RepositoryMemory:
    """
    Repository-level memory system.

    Stores and retrieves memories specific to a repository or project.
    Memories persist across sessions and provide context for the agent.
    """

    def __init__(self, repo_path: str, memory_file: str = ".tongy_memory.json"):
        """
        Initialize the repository memory.

        Args:
            repo_path: Path to the repository root
            memory_file: Name of the memory file (relative to repo root)
        """
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.memory_file = self.repo_path / memory_file
        self.memories: dict[str, list[MemoryItem]] = {}
        self._load()

    def _load(self):
        """Load memories from file."""
        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text())
                for category, items in data.items():
                    if category == "metadata":
                        continue
                    self.memories[category] = [MemoryItem(**item) for item in items]
                logger.info(f"Loaded {sum(len(v) for v in self.memories.values())} memories")
            except Exception as e:
                logger.error(f"Error loading memories: {e}")
                self.memories = {}

    def _save(self):
        """Save memories to file."""
        try:
            data = {
                "metadata": {
                    "repository": str(self.repo_path),
                    "updated_at": datetime.now().isoformat(),
                }
            }

            for category, items in self.memories.items():
                data[category] = [item.model_dump() for item in items]

            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self.memory_file.write_text(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Error saving memories: {e}")

    def add(self, key: str, value: str, category: str = "general") -> MemoryItem:
        """
        Add a new memory.

        Args:
            key: Identifier or title for the memory
            value: The actual memory content
            category: Category for organizing memories

        Returns:
            The created MemoryItem
        """
        if category not in self.memories:
            self.memories[category] = []

        # Check if memory with this key already exists
        for existing in self.memories[category]:
            if existing.key == key:
                # Update existing memory
                existing.value = value
                existing.timestamp = datetime.now().isoformat()
                self._save()
                return existing

        # Create new memory
        item = MemoryItem(
            key=key,
            value=value,
            category=category,
            timestamp=datetime.now().isoformat(),
            repository=str(self.repo_path),
        )

        self.memories[category].append(item)
        self._save()

        logger.debug(f"Added memory: {key} ({category})")
        return item

    def get(self, key: str, category: str | None = None) -> list[MemoryItem]:
        """
        Get memories by key.

        Args:
            key: Key to search for (partial match supported)
            category: Optional category filter

        Returns:
            List of matching MemoryItems
        """
        results = []

        if category:
            items = self.memories.get(category, [])
        else:
            items = [item for items in self.memories.values() for item in items]

        key_lower = key.lower()
        for item in items:
            if key_lower in item.key.lower():
                results.append(item)

        return results

    def search(self, query: str, category: str | None = None, limit: int = 10) -> list[MemoryItem]:
        """
        Search memories by query.

        Args:
            query: Search query (matches key or value)
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of matching MemoryItems
        """
        results = []

        if category:
            items = self.memories.get(category, [])
        else:
            items = [item for items in self.memories.values() for item in items]

        query_lower = query.lower()
        for item in items:
            if (query_lower in item.key.lower() or query_lower in item.value.lower()):
                results.append(item)
                if len(results) >= limit:
                    break

        return results

    def get_category(self, category: str) -> list[MemoryItem]:
        """
        Get all memories in a category.

        Args:
            category: Category name

        Returns:
            List of MemoryItems in the category
        """
        return self.memories.get(category, []).copy()

    def get_all_categories(self) -> list[str]:
        """
        Get all category names.

        Returns:
            List of category names
        """
        return list(self.memories.keys())

    def delete(self, key: str, category: str | None = None) -> bool:
        """
        Delete memories by key.

        Args:
            key: Key of memories to delete
            category: Optional category filter

        Returns:
            True if any memories were deleted
        """
        deleted = False

        if category:
            items = self.memories.get(category, [])
            original_length = len(items)
            self.memories[category] = [item for item in items if key.lower() not in item.key.lower()]
            deleted = len(self.memories[category]) < original_length
        else:
            for cat in list(self.memories.keys()):
                items = self.memories[cat]
                original_length = len(items)
                self.memories[cat] = [item for item in items if key.lower() not in item.key.lower()]
                if len(self.memories[cat]) < original_length:
                    deleted = True

        if deleted:
            self._save()
            logger.debug(f"Deleted memories with key: {key}")

        return deleted

    def get_context_prompt(self, max_items: int = 20) -> str:
        """
        Get a formatted prompt with relevant memory context.

        Args:
            max_items: Maximum number of memory items to include per category

        Returns:
            Formatted string with memory context
        """
        if not self.memories:
            return ""

        sections = ["## Repository Memory\n"]

        for category, items in sorted(self.memories.items()):
            if not items:
                continue

            sections.append(f"\n### {category.capitalize()}\n")

            # Include recent items, up to max_items
            recent_items = items[-max_items:]
            for item in recent_items:
                sections.append(f"- **{item.key}**: {item.value}")

        return "\n".join(sections)

    def clear_category(self, category: str) -> bool:
        """
        Clear all memories in a category.

        Args:
            category: Category name

        Returns:
            True if category was cleared
        """
        if category in self.memories:
            del self.memories[category]
            self._save()
            logger.debug(f"Cleared category: {category}")
            return True
        return False

    def clear_all(self):
        """Clear all memories."""
        self.memories.clear()
        self._save()
        logger.debug("Cleared all memories")

    def get_summary(self) -> str:
        """
        Get a summary of all memories.

        Returns:
            Summary string
        """
        if not self.memories:
            return "No memories stored"

        summary_lines = [f"Repository: {self.repo_path}\n"]

        for category, items in sorted(self.memories.items()):
            summary_lines.append(f"{category}: {len(items)} items")

        return "\n".join(summary_lines)
