# Tongy-Agent Examples

This directory contains example code demonstrating various features of Tongy-Agent.

## Available Examples

### 01_basic_usage.py
**基础使用示例**

Demonstrates the simplest way to use Tongy-Agent:
- Initialize the agent
- Add user requests
- Run the agent loop
- Handle responses

**Run:**
```bash
export TONGY_API_KEY="your-api-key"
python examples/01_basic_usage.py
```

### 02_tools_demo.py
**工具演示**

Shows how to work with various tools:
- **File Tools**: Read, Write, Edit, List directory
- **Bash Tool**: Execute shell commands
- **TODO Tool**: Manage task tracking
- **Sandbox**: Security controls

**Run:**
```bash
python examples/02_tools_demo.py
```
(Does not require API key - demonstrates tools directly)

### 03_mcp_integration.py
**MCP 集成演示**

Demonstrates MCP (Model Context Protocol) integration:
- Loading MCP servers
- Using MCP tools
- Managing server connections

**Run:**
```bash
python examples/03_mcp_integration.py
```

### 04_skills_demo.py
**Skills 系统演示**

Shows how to use Claude Skills:
- Loading skills from directory
- Executing skills
- Creating custom skills

**Run:**
```bash
python examples/04_skills_demo.py
```

### 05_subagent_demo.py
**SubAgent 系统演示**

Demonstrates SubAgent system:
- Creating custom sub-agents
- Using predefined sub-agents (Code, Research, Testing)
- Managing sub-agent lifecycle
- Task delegation

**Run:**
```bash
export TONGY_API_KEY="your-api-key"
python examples/05_subagent_demo.py
```

### 06_memory_demo.py
**记忆系统演示**

Shows the repository-level memory system:
- Adding memories
- Searching and retrieving
- Getting context for LLM
- Category management

**Run:**
```bash
python examples/06_memory_demo.py
```
(Does not require API key - demonstrates memory directly)

## Running the Examples

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For examples requiring API access, set your API key:
```bash
export TONGY_API_KEY="your-api-key-here"
```

Get your API key from: https://open.bigmodel.cn/

### Running Individual Examples

```bash
# Basic usage (requires API key)
python examples/01_basic_usage.py

# Tools demo (no API key needed)
python examples/02_tools_demo.py

# MCP integration (no API key needed)
python examples/03_mcp_integration.py

# Skills demo (no API key needed)
python examples/04_skills_demo.py

# SubAgent demo (requires API key)
python examples/05_subagent_demo.py

# Memory demo (no API key needed)
python examples/06_memory_demo.py
```

## Example Categories

### No API Key Required
These examples work without an API key:
- `02_tools_demo.py` - Demonstrates tool functionality
- `03_mcp_integration.py` - Shows MCP loading (placeholder)
- `04_skills_demo.py` - Shows skill loading (placeholder)
- `06_memory_demo.py` - Demonstrates memory system

### API Key Required
These examples need a valid Zhipu AI API key:
- `01_basic_usage.py` - Full agent execution
- `05_subagent_demo.py` - SubAgent delegation

## What You'll Learn

By going through these examples, you will understand:

1. **Basic Agent Usage**: How to create and run an agent
2. **Tools System**: How to use built-in tools
3. **MCP Integration**: How to extend with MCP servers
4. **Skills System**: How to use Claude Skills
5. **SubAgent System**: How to create specialized sub-agents
6. **Memory System**: How to maintain persistent context

## Next Steps

After running these examples:

1. Read the [Architecture Documentation](../docs/ARCHITECTURE.md)
2. Explore the source code in `tongy_agent/`
3. Create your own custom tools
4. Build your own specialized sub-agents

## Troubleshooting

**ImportError**: Make sure you've installed dependencies:
```bash
pip install -r requirements.txt
```

**API Key Error**: Ensure TONGY_API_KEY is set:
```bash
echo $TONGY_API_KEY
```

**Workspace Issues**: The agent will create workspace directories automatically.
