# Tongy-Agent

A Claude Code-like AI Agent powered by Zhipu GLM-4.7.

## Features

- ✅ **GLM-4.7 Integration**: Native support for Zhipu's GLM-4.7 model
- ✅ **File Operations**: Read, write, and edit files with sandbox security
- ✅ **Bash Execution**: Run shell commands with safety controls
- ✅ **TODO Management**: Built-in task tracking
- ✅ **MCP Support**: Model Context Protocol for tool extensibility
- ✅ **SubAgent System**: Delegate tasks to specialized agents
- ✅ **Memory System**: Repository-level persistent memory
- ✅ **Security Sandbox**: File access and command execution controls
- ✅ **Detailed Logging**: Full trace logging for debugging

## Quick Start

### 1. Get API Key

Get your API key from [Zhipu AI Platform](https://open.bigmodel.cn/).

### 2. Install

```bash
# Clone the repository
git clone https://github.com/yourusername/Tongy-Agent.git
cd Tongy-Agent

# Install dependencies
pip install -r requirements.txt
# or
uv sync
```

### 3. Configure

```bash
# Initialize example configuration
python -m tongy_agent.cli --init-config

# Edit configuration and set your API key
export TONGY_API_KEY="your-api-key-here"
```

### 4. Run

```bash
# Start the agent
python -m tongy_agent.cli

# Or specify workspace
python -m tongy_agent.cli --workspace ./my-project
```

## Usage Examples

### Basic Usage

```python
import asyncio
from tongy_agent.agent import Agent
from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.tools.file_tools import ReadFileTool, WriteFileTool

async def main():
    # Initialize
    llm = GLMClient(api_key="your-api-key")
    tools = [ReadFileTool(), WriteFileTool()]

    agent = Agent(
        llm_client=llm,
        system_prompt="You are a helpful coding assistant.",
        tools=tools,
        workspace_dir="./workspace",
    )

    # Use the agent
    agent.add_user_message("Create a Python hello world script")
    response = await agent.run()
    print(response)

asyncio.run(main())
```

### Using SubAgents

```python
from tongy_agent.subagent.predefined import create_code_subagent

code_agent = create_code_subagent(llm, tools)
result = await code_agent.execute("Write a function to sort a list")
```

### Memory System

```python
from tongy_agent.memory import RepositoryMemory

memory = RepositoryMemory("./my-project")
memory.add("project_name", "My Project", "general")
memory.add("key_decision", "Use PostgreSQL for database", "decisions")

# Get context for LLM
context = memory.get_context_prompt()
```

## Configuration

Configuration is loaded from (in priority order):
1. Command-line `--config` argument
2. `./tongy_agent/config/config.yaml`
3. `~/.tongy-agent/config/config.yaml`
4. Environment variables (`TONGY_*`)

### Environment Variables

- `TONGY_API_KEY`: API key for Zhipu AI
- `TONGY_API_BASE`: API base URL
- `TONGY_MODEL`: Model name (default: glm-4.7)
- `TONGY_WORKSPACE`: Workspace directory
- `TONGY_MAX_STEPS`: Maximum agent steps
- `TONGY_VERBOSE`: Enable verbose logging

## CLI Commands

- `/help` - Show help
- `/quit` - Exit the agent
- `/clear` - Clear the screen
- `/config` - Show configuration
- `/workspace` - Show workspace info
- `/todos` - Show current TODOs

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black tongy_agent/
ruff check tongy_agent/
```

### Type Checking

```bash
mypy tongy_agent/
```

## Architecture

```
Tongy-Agent/
├── tongy_agent/          # Main package
│   ├── agent.py          # Core Agent
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration
│   ├── llm/              # LLM clients
│   ├── tools/            # Tool implementations
│   ├── subagent/         # SubAgent system
│   ├── memory.py         # Memory system
│   ├── sandbox.py        # Security sandbox
│   └── logger.py         # Logging
├── tests/                # Test suite
├── examples/             # Usage examples
└── docs/                 # Documentation
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Requirements

- Python 3.10+
- Zhipu AI API key

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [MiniMax-AI/Mini-Agent](https://github.com/MiniMax-AI/Mini-Agent)
- Uses Zhipu GLM-4.7 model
- Compatible with Claude Skills format

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
