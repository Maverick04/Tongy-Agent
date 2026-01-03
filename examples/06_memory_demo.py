"""
Memory system demo for Tongy-Agent.

This example demonstrates the repository-level memory system.
"""

import asyncio
import tempfile
from pathlib import Path

from tongy_agent.memory import RepositoryMemory


async def main():
    """Demonstrate the memory system."""

    # Create a temporary repository
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temporary repository: {tmpdir}\n")

        # Initialize memory
        memory = RepositoryMemory(tmpdir)

        # Add some memories
        print("Adding memories...")
        memory.add("project_name", "Tongy-Agent", "general")
        memory.add("primary_language", "Python", "general")
        memory.add("framework", "Pydantic", "technical")
        memory.add("llm", "GLM-4.7", "technical")
        memory.add("key_feature", "Sandbox security", "features")

        # Retrieve memories
        print("\nRetrieving memories:")
        items = memory.get("project")
        for item in items:
            print(f"  - {item.key}: {item.value} ({item.category})")

        # Search memories
        print("\nSearching for 'Python':")
        items = memory.search("Python")
        for item in items:
            print(f"  - {item.key}: {item.value}")

        # Get category
        print("\nTechnical category:")
        tech_items = memory.get_category("technical")
        for item in tech_items:
            print(f"  - {item.key}: {item.value}")

        # Get context prompt
        print("\nContext prompt for LLM:")
        context = memory.get_context_prompt()
        print(context)

        # Get summary
        print("\nMemory summary:")
        print(memory.get_summary())


if __name__ == "__main__":
    asyncio.run(main())
