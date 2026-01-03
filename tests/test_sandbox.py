"""
Tests for the sandbox system.
"""

import pytest
from pathlib import Path
import tempfile

from tongy_agent.sandbox import FileSandbox, CommandSandbox, Sandbox
from tongy_agent.schema.schema import SandboxConfig


class TestFileSandbox:
    """Tests for FileSandbox."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sandbox_config(self, temp_dir):
        """Create a sandbox config for testing."""
        return SandboxConfig(
            allowed_paths=[temp_dir],
            forbidden_paths=[],
            max_file_size=1024 * 1024,  # 1MB
        )

    @pytest.fixture
    def file_sandbox(self, sandbox_config):
        """Create a file sandbox for testing."""
        return FileSandbox(sandbox_config)

    def test_allowed_path(self, file_sandbox, temp_dir):
        """Test that allowed paths are accepted."""
        allowed, reason = file_sandbox.is_allowed(temp_dir)
        assert allowed
        assert reason is None

    def test_forbidden_path(self, file_sandbox):
        """Test that non-allowed paths are rejected."""
        forbidden = "/etc/passwd"
        allowed, reason = file_sandbox.is_allowed(forbidden)
        assert not allowed
        assert "Access denied" in reason

    def test_file_size_check(self, file_sandbox, temp_dir):
        """Test file size checking."""
        # Create a small file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("small content")

        allowed, reason = file_sandbox.check_file_size(test_file)
        assert allowed
        assert reason is None


class TestCommandSandbox:
    """Tests for CommandSandbox."""

    @pytest.fixture
    def sandbox_config(self):
        """Create a sandbox config for testing."""
        return SandboxConfig(
            forbidden_commands=["rm", "dd"],
        )

    @pytest.fixture
    def command_sandbox(self, sandbox_config):
        """Create a command sandbox for testing."""
        return CommandSandbox(sandbox_config)

    def test_allowed_command(self, command_sandbox):
        """Test that allowed commands are accepted."""
        allowed, reason = command_sandbox.is_allowed("ls -la")
        assert allowed
        assert reason is None

    def test_forbidden_command(self, command_sandbox):
        """Test that forbidden commands are rejected."""
        allowed, reason = command_sandbox.is_allowed("rm -rf /")
        assert not allowed
        assert "forbidden" in reason.lower()


class TestSandbox:
    """Tests for the combined Sandbox."""

    @pytest.fixture
    def sandbox(self):
        """Create a sandbox for testing."""
        config = SandboxConfig(
            allowed_paths=["./workspace"],
            forbidden_commands=["rm"],
        )
        return Sandbox(config)

    def test_file_sandbox_integration(self, sandbox):
        """Test file sandbox integration."""
        assert sandbox.file_sandbox is not None

    def test_command_sandbox_integration(self, sandbox):
        """Test command sandbox integration."""
        assert sandbox.command_sandbox is not None

    def test_configure_from_workspace(self, sandbox, tmp_path):
        """Test configuring sandbox from workspace."""
        sandbox.configure_from_workspace(str(tmp_path))

        # Check that workspace is in allowed paths
        allowed, _ = sandbox.is_file_allowed(tmp_path)
        assert allowed
