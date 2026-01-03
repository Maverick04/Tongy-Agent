"""
Integration tests for Tongy-Agent.

These tests verify the end-to-end functionality of the agent system.
"""

import pytest
import tempfile
from pathlib import Path


class TestAgentIntegration:
    """Integration tests for the Agent."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_agent_initialization(self, temp_workspace):
        """Test that the agent can be initialized."""
        from tongy_agent.agent import Agent
        from tongy_agent.llm.glm_client import GLMClient
        from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool

        # Create a mock client (don't use real API)
        class MockGLMClient(GLMClient):
            def __init__(self):
                self.api_key = "test"
                self.model = "test"
                self.api_base = "https://test"

            async def generate(self, messages, tools=None):
                from tongy_agent.schema.schema import LLMResponse
                return LLMResponse(
                    content="Hello! How can I help?",
                    tool_calls=None,
                    finish_reason="stop",
                )

        llm = MockGLMClient()
        tools = [ReadFileTool(), WriteFileTool()]

        agent = Agent(
            llm_client=llm,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=temp_workspace,
        )

        assert agent is not None
        assert len(agent.tools) == 2

    @pytest.mark.asyncio
    async def test_file_workflow(self, temp_workspace):
        """Test a complete file workflow."""
        from tongy_agent.tools.file_tools import WriteFileTool, ReadFileTool, EditFileTool

        write_tool = WriteFileTool(sandbox=None)
        read_tool = ReadFileTool(sandbox=None)
        edit_tool = EditFileTool(sandbox=None)

        # Write a file
        test_file = Path(temp_workspace) / "test.txt"
        result = await write_tool.execute(
            path=str(test_file),
            content="Hello World"
        )
        assert result.success
        assert test_file.exists()

        # Read the file
        result = await read_tool.execute(path=str(test_file))
        assert result.success
        assert result.content == "Hello World"

        # Edit the file
        result = await edit_tool.execute(
            path=str(test_file),
            old_string="Hello",
            new_string="Hi"
        )
        assert result.success

        # Verify edit
        result = await read_tool.execute(path=str(test_file))
        assert result.content == "Hi World"


class TestMemoryIntegration:
    """Integration tests for the memory system."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_memory_persistence(self, temp_repo):
        """Test that memory persists across instances."""
        from tongy_agent.memory import RepositoryMemory

        # Create first instance and add memory
        memory1 = RepositoryMemory(temp_repo)
        memory1.add("test", "value1", "category1")

        # Create second instance and verify memory persists
        memory2 = RepositoryMemory(temp_repo)
        items = memory2.get("test")

        assert len(items) == 1
        assert items[0].value == "value1"

    def test_memory_categories(self, temp_repo):
        """Test memory categories."""
        from tongy_agent.memory import RepositoryMemory

        memory = RepositoryMemory(temp_repo)

        memory.add("item1", "value1", "cat1")
        memory.add("item2", "value2", "cat2")
        memory.add("item3", "value3", "cat1")

        cat1_items = memory.get_category("cat1")
        cat2_items = memory.get_category("cat2")

        assert len(cat1_items) == 2
        assert len(cat2_items) == 1


class TestSandboxIntegration:
    """Integration tests for the sandbox."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_complete_sandbox_workflow(self, temp_dir):
        """Test sandbox with file and command operations."""
        from tongy_agent.sandbox import Sandbox
        from tongy_agent.schema.schema import SandboxConfig

        config = SandboxConfig(
            allowed_paths=[temp_dir],
            forbidden_commands=["rm"],
        )
        sandbox = Sandbox(config)

        # Test file access
        allowed_file = Path(temp_dir) / "allowed.txt"
        assert sandbox.is_file_allowed(allowed_file)[0] == True

        forbidden_file = Path("/etc/passwd")
        assert sandbox.is_file_allowed(forbidden_file)[0] == False

        # Test command filtering
        assert sandbox.is_command_allowed("ls")[0] == True
        assert sandbox.is_command_allowed("rm -rf /")[0] == False


class TestConfigIntegration:
    """Integration tests for configuration."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_config_from_file(self, temp_config_dir):
        """Test loading configuration from file."""
        from tongy_agent.config import ConfigManager
        import yaml

        config_file = Path(temp_config_dir) / "config.yaml"
        config_data = {
            "llm": {
                "api_key": "test-key",
                "model": "glm-4.7",
            },
            "agent": {
                "max_steps": 100,
                "workspace_dir": "./test_workspace",
            },
        }

        config_file.write_text(yaml.dump(config_data))

        manager = ConfigManager(str(config_file))
        config = manager.config

        assert config.llm.api_key == "test-key"
        assert config.llm.model == "glm-4.7"
        assert config.agent.max_steps == 100

    def test_config_env_override(self, temp_config_dir, monkeypatch):
        """Test environment variable override."""
        from tongy_agent.config import ConfigManager

        # Set environment variable
        monkeypatch.setenv("TONGY_API_KEY", "env-key")

        manager = ConfigManager()
        config = manager.config

        # Should use env variable
        # Note: This will use default config if no file exists
        # The env override is applied in _override_with_env
        assert "env-key" in str(config.llm.api_key) or config.llm.api_key == "env-key"
