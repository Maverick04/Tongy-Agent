"""
Sandbox security system for Tongy-Agent.

Provides file access and command execution controls to ensure safe operation.
"""

import logging
from pathlib import Path
from typing import Any

from tongy_agent.schema.schema import SandboxConfig

logger = logging.getLogger(__name__)


class FileSandbox:
    """
    File access sandbox.

    Controls which files and directories the agent can access.
    """

    def __init__(self, config: SandboxConfig):
        """
        Initialize the file sandbox.

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self._resolve_paths()

    def _resolve_paths(self):
        """Resolve all configured paths to absolute paths."""
        self.allowed_paths = [Path(p).expanduser().resolve() for p in self.config.allowed_paths]
        self.forbidden_paths = [Path(p).expanduser().resolve() for p in self.config.forbidden_paths]

    def is_allowed(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Check if a path is allowed to be accessed.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        try:
            path = Path(path).expanduser().resolve()

            # Check forbidden paths first
            for forbidden in self.forbidden_paths:
                try:
                    path.relative_to(forbidden)
                    return False, f"Access denied: path is in forbidden list ({forbidden})"
                except ValueError:
                    # Path is not under this forbidden path
                    pass

            # If no allowed paths are specified, allow everything (except forbidden)
            if not self.allowed_paths:
                return True, None

            # Check if path is under any allowed path
            for allowed in self.allowed_paths:
                try:
                    path.relative_to(allowed)
                    return True, None
                except ValueError:
                    # Path is not under this allowed path
                    pass

            # Path is not under any allowed path
            allowed_list = ", ".join(str(p) for p in self.allowed_paths)
            return False, f"Access denied: path not in allowed list ({allowed_list})"

        except Exception as e:
            logger.error(f"Error checking path access: {e}")
            return False, f"Error checking path access: {e}"

    def check_file_size(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Check if a file is within the size limit.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        try:
            path = Path(path).expanduser().resolve()

            if not path.exists() or not path.is_file():
                # Non-existent files are OK (will be created)
                return True, None

            size = path.stat().st_size
            if size > self.config.max_file_size:
                size_mb = size / (1024 * 1024)
                limit_mb = self.config.max_file_size / (1024 * 1024)
                return False, f"File too large: {size_mb:.2f}MB > {limit_mb:.2f}MB"

            return True, None

        except Exception as e:
            logger.error(f"Error checking file size: {e}")
            return False, f"Error checking file size: {e}"


class CommandSandbox:
    """
    Command execution sandbox.

    Controls which commands the agent can execute.
    """

    def __init__(self, config: SandboxConfig):
        """
        Initialize the command sandbox.

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self._build_command_sets()

    def _build_command_sets(self):
        """Build sets of allowed and forbidden commands."""
        self.allowed_commands = set(self.config.allowed_commands)
        self.forbidden_commands = set(self.config.forbidden_commands)

        # Add default dangerous commands to forbidden list
        if not self.config.forbidden_commands:
            self.forbidden_commands.update({
                "rm", "rmdir", "del", "delete",
                "format", "mkfs", "fdisk",
                "dd", "shutdown", "reboot", "halt", "poweroff",
                "kill", "killall",
                "su", "sudo", "passwd",
                "chmod", "chown",
                "iptables", "ufw",
            })

    def is_allowed(self, command: str) -> tuple[bool, str | None]:
        """
        Check if a command is allowed to execute.

        Args:
            command: Command string to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Extract the base command name
        cmd_name = self._extract_command_name(command)

        # Check forbidden commands first
        if cmd_name in self.forbidden_commands:
            return False, f"Command forbidden for security reasons: {cmd_name}"

        # If allowed commands are specified, check against them
        if self.allowed_commands:
            if cmd_name not in self.allowed_commands:
                return False, f"Command not in allowed list: {cmd_name}"

        return True, None

    def is_command_allowed(self, command: str) -> tuple[bool, str | None]:
        """Alias for is_allowed for compatibility with tools."""
        return self.is_allowed(command)

    def _extract_command_name(self, command: str) -> str:
        """
        Extract the base command name from a command string.

        Args:
            command: Command string

        Returns:
            Base command name
        """
        # Remove leading/trailing whitespace
        command = command.strip()

        # Handle pipes and redirects by taking only the first command
        for separator in ("|", ">", "<", "&", ";;"):
            if separator in command:
                command = command.split(separator)[0].strip()

        # Extract the first word (command name)
        parts = command.split()
        if not parts:
            return ""

        # Handle paths (e.g., /usr/bin/python -> python)
        cmd_name = parts[0]
        if "/" in cmd_name:
            cmd_name = cmd_name.split("/")[-1]

        return cmd_name


class Sandbox:
    """
    Combined sandbox for both file and command access control.

    Provides a unified interface for all sandbox security checks.
    """

    def __init__(self, config: SandboxConfig):
        """
        Initialize the sandbox.

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self.file_sandbox = FileSandbox(config)
        self.command_sandbox = CommandSandbox(config)

    def is_allowed(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Check if file access is allowed (alias for is_file_allowed).

        Args:
            path: Path to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        return self.file_sandbox.is_allowed(path)

    def is_file_allowed(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Check if file access is allowed.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        return self.file_sandbox.is_allowed(path)

    def check_file_size(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Check if file is within size limit.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        return self.file_sandbox.check_file_size(path)

    def is_command_allowed(self, command: str) -> tuple[bool, str | None]:
        """
        Check if command execution is allowed.

        Args:
            command: Command string to check

        Returns:
            Tuple of (is_allowed, error_message)
        """
        return self.command_sandbox.is_allowed(command)

    def configure_from_workspace(self, workspace_dir: str):
        """
        Configure sandbox to allow access to workspace directory.

        Args:
            workspace_dir: Path to workspace directory
        """
        workspace_path = Path(workspace_dir).expanduser().resolve()

        # Add workspace to allowed paths
        if str(workspace_path) not in [str(p) for p in self.file_sandbox.allowed_paths]:
            self.file_sandbox.allowed_paths.append(workspace_path)
            self.file_sandbox._resolve_paths()

        logger.info(f"Sandbox configured for workspace: {workspace_path}")
