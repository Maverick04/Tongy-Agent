"""
MCP (Model Context Protocol) integration demo.

Shows how to load and use MCP servers.
"""

import asyncio
from tongy_agent.tools.mcp_loader import MCPLoader, load_mcp_tools


async def demo_mcp_loader():
    """Demonstrate MCP loader functionality."""
    print("=== MCP Loader Demo ===\n")

    # Create loader
    loader = MCPLoader()

    if not loader.is_available():
        print("MCP is not available. Install anthropic package:")
        print("  pip install anthropic")
        return

    print("MCP is available!\n")

    # Example: Load an MCP server
    # This is a placeholder - actual servers would be configured
    servers_config = [
        {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
        },
    ]

    print(f"Loading {len(servers_config)} MCP servers...")
    loaded = await loader.load_from_config(servers_config)
    print(f"Successfully loaded: {loaded} servers\n")

    # Discover tools
    tools = await loader.discover_tools()
    print(f"Discovered {len(tools)} tools from MCP servers\n")

    # Get tool names
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Close all connections
    await loader.close_all()
    print("\nClosed all MCP connections")


async def demo_load_mcp_tools():
    """Demonstrate convenience function for loading MCP tools."""
    print("=== Load MCP Tools Demo ===\n")

    servers_config = [
        {
            "name": "example",
            "command": "echo",
            "args": ["example"],
        },
    ]

    tools = await load_mcp_tools(servers_config)
    print(f"Loaded {len(tools)} MCP tools\n")


async def main():
    """Run MCP demos."""
    print("Tongy-Agent MCP Integration Demo\n")
    print("=" * 50)

    await demo_mcp_loader()
    print("\n")
    await demo_load_mcp_tools()

    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
