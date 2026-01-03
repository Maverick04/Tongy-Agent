"""
MCP (Model Context Protocol) server loader for Tongy-Agent.

Integrates MCP servers to provide additional tools to the agent.
"""

import asyncio
import json
import logging
from typing import Any

try:
    from anthropic import Anthropic
    from anthropic.mcp import MCPServer
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from tongy_agent.schema.schema import ToolResult
from tongy_agent.tools.base import Tool

logger = logging.getLogger(__name__)


class MCPTool(Tool):
    """Wrapper for MCP tools."""

    def __init__(self, name: str, description: str, parameters: dict[str, Any], mcp_server: Any):
        """
        Initialize an MCP tool wrapper.

        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            mcp_server: MCP server instance
        """
        self._name = name
        self._description = description
        self._parameters = parameters
        self.mcp_server = mcp_server

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the MCP tool."""
        try:
            # Call the MCP tool
            result = await self.mcp_server.call_tool(self._name, kwargs)

            # Parse result
            if isinstance(result, dict):
                if "content" in result:
                    content = result["content"]
                elif "result" in result:
                    content = json.dumps(result["result"])
                else:
                    content = json.dumps(result)
            else:
                content = str(result)

            return ToolResult(success=True, content=content)

        except Exception as e:
            logger.error(f"MCP tool {self._name} failed: {e}")
            return ToolResult(
                success=False,
                content="",
                error=f"MCP tool error: {e}",
            )


class MCPLoader:
    """
    Loader for MCP servers.

    Manages connections to MCP servers and exposes their tools.
    """

    def __init__(self):
        """Initialize the MCP loader."""
        if not MCP_AVAILABLE:
            logger.warning("anthropic package not available. MCP integration disabled.")
            self.enabled = False
            return

        self.enabled = True
        self.servers: dict[str, Any] = {}
        self.tools: dict[str, MCPTool] = {}

    def is_available(self) -> bool:
        """Check if MCP is available."""
        return MCP_AVAILABLE

    async def load_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> bool:
        """
        Load an MCP server.

        Args:
            name: Server name
            command: Command to start the server
            args: Command arguments
            env: Environment variables

        Returns:
            True if server was loaded successfully
        """
        if not self.enabled:
            logger.warning("MCP not available, skipping server load")
            return False

        try:
            # Create MCP server instance
            # Note: This is a simplified implementation
            # In production, you would use the actual MCP SDK
            logger.info(f"Loading MCP server: {name} ({command})")

            # Placeholder for actual MCP server connection
            # The actual implementation would depend on the MCP SDK version
            self.servers[name] = {
                "command": command,
                "args": args or [],
                "env": env or {},
                "connected": True,
            }

            return True

        except Exception as e:
            logger.error(f"Failed to load MCP server {name}: {e}")
            return False

    async def load_from_config(self, servers_config: list[dict[str, Any]]) -> int:
        """
        Load multiple MCP servers from configuration.

        Args:
            servers_config: List of server configurations

        Returns:
            Number of servers loaded successfully
        """
        if not self.enabled:
            return 0

        loaded_count = 0

        for config in servers_config:
            name = config.get("name", "unnamed")
            command = config.get("command")
            args = config.get("args", [])
            env = config.get("env", {})

            if not command:
                logger.warning(f"MCP server {name} missing command, skipping")
                continue

            success = await self.load_server(name, command, args, env)
            if success:
                loaded_count += 1

        logger.info(f"Loaded {loaded_count}/{len(servers_config)} MCP servers")
        return loaded_count

    async def discover_tools(self) -> list[MCPTool]:
        """
        Discover tools from all loaded MCP servers.

        Returns:
            List of MCP tools
        """
        if not self.enabled or not self.servers:
            return []

        tools = []

        for server_name, server_info in self.servers.items():
            try:
                # Discover tools from this server
                # This is a placeholder - actual implementation would query the server
                server_tools = await self._discover_server_tools(server_name)
                tools.extend(server_tools)

            except Exception as e:
                logger.error(f"Failed to discover tools from {server_name}: {e}")

        # Store tools by name
        for tool in tools:
            self.tools[tool.name] = tool

        logger.info(f"Discovered {len(tools)} tools from {len(self.servers)} MCP servers")
        return tools

    async def _discover_server_tools(self, server_name: str) -> list[MCPTool]:
        """
        Discover tools from a specific server.

        Args:
            server_name: Server name

        Returns:
            List of MCP tools from the server
        """
        # Placeholder implementation
        # In production, this would query the actual MCP server
        return []

    def get_tools(self) -> list[Tool]:
        """Get all discovered MCP tools."""
        return list(self.tools.values())

    async def close_all(self):
        """Close all MCP server connections."""
        for name, server in self.servers.items():
            try:
                # Close server connection
                if hasattr(server, "close"):
                    await server.close()
            except Exception as e:
                logger.error(f"Error closing MCP server {name}: {e}")

        self.servers.clear()
        self.tools.clear()


# Convenience function to create and load MCP tools
async def load_mcp_tools(servers_config: list[dict[str, Any]]) -> list[Tool]:
    """
    Load MCP tools from server configurations.

    Args:
        servers_config: List of MCP server configurations

    Returns:
        List of loaded tools
    """
    loader = MCPLoader()

    if not loader.is_available():
        logger.warning("MCP not available, no tools loaded")
        return []

    # Load servers
    await loader.load_from_config(servers_config)

    # Discover tools
    tools = await loader.discover_tools()

    return tools
