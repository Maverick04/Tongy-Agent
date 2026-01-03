"""
Skills system for Tongy-Agent.

Provides a way to load and execute Claude-compatible skills.
"""

import json
import logging
from pathlib import Path
from typing import Any

from tongy_agent.schema.schema import ToolResult
from tongy_agent.tools.base import Tool

logger = logging.getLogger(__name__)


class SkillTool(Tool):
    """Wrapper for executing Claude Skills."""

    def __init__(
        self,
        name: str,
        description: str,
        skill_path: str,
    ):
        """
        Initialize a skill tool.

        Args:
            name: Skill name
            description: Skill description
            skill_path: Path to the skill directory
        """
        self._name = name
        self._description = description
        self.skill_path = Path(skill_path)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task description for the skill",
                },
            },
            "required": ["task"],
        }

    async def execute(self, task: str) -> ToolResult:
        """Execute the skill."""
        try:
            # Check if skill has an API endpoint
            api_file = self.skill_path / "api.json"

            if api_file.exists():
                # Load API configuration
                with open(api_file) as f:
                    api_config = json.load(f)

                # For now, return a placeholder
                # In production, this would call the actual skill API
                return ToolResult(
                    success=True,
                    content=f"Skill '{self._name}' would execute: {task}\n"
                    f"API: {api_config.get('endpoint', 'N/A')}",
                )
            else:
                # No API found, return basic info
                return ToolResult(
                    success=True,
                    content=f"Skill '{self._name}' loaded from {self.skill_path}\n"
                    f"Task: {task}",
                )

        except Exception as e:
            logger.error(f"Skill {self._name} failed: {e}")
            return ToolResult(
                success=False,
                content="",
                error=f"Skill error: {e}",
            )


class SkillLoader:
    """
    Loader for Claude Skills.

    Discovers and loads skills from a skills directory.
    """

    def __init__(self, skills_path: str | None = None):
        """
        Initialize the skill loader.

        Args:
            skills_path: Path to skills directory
        """
        self.skills_path = Path(skills_path) if skills_path else None
        self.skills: dict[str, SkillTool] = {}

    def discover_skills(self) -> list[SkillTool]:
        """
        Discover available skills.

        Returns:
            List of discovered skills
        """
        if not self.skills_path or not self.skills_path.exists():
            logger.info("No skills directory found")
            return []

        skills = []

        # Look for skill directories
        for item in self.skills_path.iterdir():
            if item.is_dir():
                # Check if this is a valid skill directory
                manifest_file = item / "manifest.json"

                if manifest_file.exists():
                    try:
                        with open(manifest_file) as f:
                            manifest = json.load(f)

                        name = manifest.get("name", item.name)
                        description = manifest.get(
                            "description",
                            f"Skill: {name}",
                        )

                        skill = SkillTool(
                            name=name,
                            description=description,
                            skill_path=str(item),
                        )

                        skills.append(skill)
                        self.skills[name] = skill

                        logger.info(f"Discovered skill: {name}")

                    except Exception as e:
                        logger.error(f"Error loading skill from {item}: {e}")

        logger.info(f"Discovered {len(skills)} skills")
        return skills

    def get_skills(self) -> list[SkillTool]:
        """Get all loaded skills."""
        return list(self.skills.values())

    def get_skill(self, name: str) -> SkillTool | None:
        """Get a specific skill by name."""
        return self.skills.get(name)

    def get_skill_names(self) -> list[str]:
        """Get names of all loaded skills."""
        return list(self.skills.keys())


async def load_skills(skills_path: str | None = None) -> list[Tool]:
    """
    Load skills from a directory.

    Args:
        skills_path: Path to skills directory

    Returns:
        List of skill tools
    """
    loader = SkillLoader(skills_path)
    return loader.discover_skills()
