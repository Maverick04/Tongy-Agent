"""
Skills system demonstration for Tongy-Agent.

Shows how to load and use Claude Skills.
"""

import asyncio
import tempfile
import json
from pathlib import Path

from tongy_agent.tools.skill_loader import SkillLoader, load_skills


async def demo_skill_loader():
    """Demonstrate skill loader."""
    print("=== Skill Loader Demo ===\n")

    # Create a temporary skills directory with example skills
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()

        # Create example skill
        example_skill = skills_dir / "python_helper"
        example_skill.mkdir()

        # Create skill manifest
        manifest = {
            "name": "python_helper",
            "description": "Provides Python programming assistance",
            "version": "1.0.0",
        }
        (example_skill / "manifest.json").write_text(json.dumps(manifest, indent=2))

        # Create skill API
        api_config = {
            "endpoint": "https://api.example.com/skills/python_helper",
            "method": "POST",
        }
        (example_skill / "api.json").write_text(json.dumps(api_config, indent=2))

        # Load skills
        loader = SkillLoader(str(skills_dir))
        skills = loader.discover_skills()

        print(f"Discovered {len(skills)} skills:\n")
        for skill in skills:
            print(f"  - {skill.name}: {skill.description}")

        # Get skill names
        print(f"\nSkill names: {loader.get_skill_names()}")

        # Execute a skill
        if skills:
            print("\nExecuting skill...")
            result = await skills[0].execute(task="Help me write a Python function")
            print(f"Result: {result.content}")


async def demo_load_skills():
    """Demonstrate convenience function for loading skills."""
    print("=== Load Skills Demo ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir()

        # Create example skill
        example_skill = skills_dir / "test_skill"
        example_skill.mkdir()

        manifest = {
            "name": "test_skill",
            "description": "A test skill",
        }
        (example_skill / "manifest.json").write_text(json.dumps(manifest, indent=2))

        # Load skills
        tools = await load_skills(str(skills_dir))
        print(f"Loaded {len(tools)} skill tools\n")


async def main():
    """Run skills demos."""
    print("Tongy-Agent Skills System Demo\n")
    print("=" * 50)

    await demo_skill_loader()
    print("\n")
    await demo_load_skills()

    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
