"""
Configuration management for Tongy-Agent.

Handles loading and managing configuration from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from tongy_agent.schema.schema import (
    AgentConfig,
    Config,
    LLMConfig,
    LLMProvider,
    RetryConfig,
    SandboxConfig,
    ToolsConfig,
)

load_dotenv()


class ConfigManager:
    """
    Configuration manager for Tongy-Agent.

    Loads configuration from YAML files with fallback to environment variables.
    """

    # Default configuration search paths
    DEFAULT_SEARCH_PATHS = [
        "./tongy_agent/config/config.yaml",
        "~/.tongy-agent/config/config.yaml",
        "~/.config/tongy-agent/config.yaml",
    ]

    def __init__(self, config_path: str | None = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """
        Load configuration from file or environment variables.

        Returns:
            Config object
        """
        config_data = {}

        # Try to load from file
        if self.config_path:
            config_data = self._load_from_file(self.config_path)
        else:
            # Try default search paths
            for path in self.DEFAULT_SEARCH_PATHS:
                expanded = Path(path).expanduser()
                if expanded.exists():
                    config_data = self._load_from_file(expanded)
                    break

        # Override with environment variables
        config_data = self._override_with_env(config_data)

        # Build Config object
        return self._build_config(config_data)

    def _load_from_file(self, path: str | Path) -> dict[str, Any]:
        """
        Load configuration from a YAML file.

        Args:
            path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        path = Path(path).expanduser()

        if not path.exists():
            return {}

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            return data
        except Exception as e:
            raise ValueError(f"Error loading config from {path}: {e}")

    def _override_with_env(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """
        Override configuration with environment variables.

        Environment variables:
        - TONGY_API_KEY: API key for LLM
        - TONGY_API_BASE: Base URL for API
        - TONGY_MODEL: Model name
        - TONGY_WORKSPACE: Workspace directory
        - TONGY_MAX_STEPS: Maximum steps
        - TONGY_VERBOSE: Enable verbose logging

        Args:
            config_data: Existing configuration data

        Returns:
            Updated configuration data
        """
        # LLM configuration
        if "llm" not in config_data:
            config_data["llm"] = {}

        if os.getenv("TONGY_API_KEY"):
            config_data["llm"]["api_key"] = os.getenv("TONGY_API_KEY")
        if os.getenv("TONGY_API_BASE"):
            config_data["llm"]["api_base"] = os.getenv("TONGY_API_BASE")
        if os.getenv("TONGY_MODEL"):
            config_data["llm"]["model"] = os.getenv("TONGY_MODEL")

        # Agent configuration
        if "agent" not in config_data:
            config_data["agent"] = {}

        if os.getenv("TONGY_WORKSPACE"):
            config_data["agent"]["workspace_dir"] = os.getenv("TONGY_WORKSPACE")
        if os.getenv("TONGY_MAX_STEPS"):
            config_data["agent"]["max_steps"] = int(os.getenv("TONGY_MAX_STEPS"))

        # Verbose mode
        if os.getenv("TONGY_VERBOSE"):
            config_data["agent"]["verbose"] = os.getenv("TONGY_VERBOSE").lower() == "true"

        return config_data

    def _build_config(self, data: dict[str, Any]) -> Config:
        """
        Build Config object from raw data.

        Args:
            data: Configuration dictionary

        Returns:
            Config object
        """
        # Build LLM config
        llm_data = data.get("llm", {})
        llm_config = LLMConfig(
            provider=LLMProvider(llm_data.get("provider", "zhipu")),
            api_key=llm_data.get("api_key", ""),
            api_base=llm_data.get("api_base", "https://open.bigmodel.cn/api/paas/v4/"),
            model=llm_data.get("model", "glm-4.7"),
            timeout=llm_data.get("timeout", 120),
            max_tokens=llm_data.get("max_tokens", 16384),
            temperature=llm_data.get("temperature", 0.7),
            retry=RetryConfig(**llm_data.get("retry", {})),
        )

        # Build agent config
        agent_data = data.get("agent", {})
        agent_config = AgentConfig(
            max_steps=agent_data.get("max_steps", 50),
            token_limit=agent_data.get("token_limit", 80000),
            workspace_dir=agent_data.get("workspace_dir", "./workspace"),
            enable_memory=agent_data.get("enable_memory", True),
            enable_sandbox=agent_data.get("enable_sandbox", True),
            verbose=agent_data.get("verbose", False),
        )

        # Build tools config
        tools_data = data.get("tools", {})
        tools_config = ToolsConfig(
            enable_mcp=tools_data.get("enable_mcp", True),
            enable_skills=tools_data.get("enable_skills", True),
            mcp_servers=tools_data.get("mcp_servers", []),
            skills_path=tools_data.get("skills_path"),
        )

        # Build sandbox config
        sandbox_data = data.get("sandbox", {})
        sandbox_config = SandboxConfig(
            allowed_paths=sandbox_data.get("allowed_paths", []),
            forbidden_paths=sandbox_data.get("forbidden_paths", []),
            max_file_size=sandbox_data.get("max_file_size", 10 * 1024 * 1024),
            allowed_commands=sandbox_data.get("allowed_commands", []),
            forbidden_commands=sandbox_data.get("forbidden_commands", []),
            allow_network_access=sandbox_data.get("allow_network_access", False),
        )

        return Config(
            llm=llm_config,
            agent=agent_config,
            tools=tools_config,
            sandbox=sandbox_config,
        )

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check API key
        if not self.config.llm.api_key:
            errors.append("LLM API key is required (set TONGY_API_KEY environment variable)")

        # Check workspace directory
        workspace = Path(self.config.agent.workspace_dir).expanduser()
        if not workspace.exists():
            try:
                workspace.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create workspace directory: {e}")

        return errors

    def get_system_prompt(self) -> str:
        """
        Load the system prompt from file.

        Returns:
            System prompt string
        """
        # Try to load from config directory
        for search_path in [
            Path("./tongy_agent/config/system_prompt.md"),
            Path("~/.tongy-agent/config/system_prompt.md").expanduser(),
            Path("~/.config/tongy-agent/system_prompt.md").expanduser(),
        ]:
            if search_path.exists():
                return search_path.read_text()

        # Return default prompt
        return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Return the default system prompt."""
        return """# Tongy-Agent

You are Tongy-Agent, an AI programming assistant powered by Zhipu GLM-4.7.

## Capabilities

You can help users with:
- Reading, writing, and editing files
- Executing bash commands
- Managing tasks with TODO tracking
- Searching and analyzing code
- Implementing new features
- Debugging and fixing issues

## Guidelines

1. **Be Precise**: Provide accurate, well-reasoned responses
2. **Use Tools**: Leverage available tools to accomplish tasks
3. **Stay Focused**: Address the user's request directly
4. **Think Step by Step**: Break down complex tasks
5. **Communicate Clearly**: Explain your actions and reasoning

## Safety

- Always verify file paths before operations
- Use sandbox restrictions for security
- Ask for clarification when uncertain
- Never execute destructive commands without confirmation
"""

    def save_example_config(self, path: str | Path):
        """
        Save an example configuration file.

        Args:
            path: Path to save the example config
        """
        path = Path(path)

        example_config = {
            "llm": {
                "provider": "zhipu",
                "api_key": "YOUR_API_KEY_HERE",
                "api_base": "https://open.bigmodel.cn/api/paas/v4/",
                "model": "glm-4.7",
                "timeout": 120,
                "max_tokens": 16384,
                "temperature": 0.7,
            },
            "agent": {
                "max_steps": 50,
                "token_limit": 80000,
                "workspace_dir": "./workspace",
                "enable_memory": True,
                "enable_sandbox": True,
                "verbose": False,
            },
            "tools": {
                "enable_mcp": True,
                "enable_skills": True,
                "mcp_servers": [],
                "skills_path": None,
            },
            "sandbox": {
                "allowed_paths": [],
                "forbidden_paths": [],
                "max_file_size": 10485760,
                "allowed_commands": [],
                "forbidden_commands": ["rm", "rmdir", "del", "format", "dd"],
                "allow_network_access": False,
            },
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(example_config, f, default_flow_style=False, sort_keys=False)


def load_config(config_path: str | None = None) -> Config:
    """
    Convenience function to load configuration.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Config object
    """
    manager = ConfigManager(config_path)
    return manager.config
