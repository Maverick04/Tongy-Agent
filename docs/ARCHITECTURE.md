# Tongy-Agent Architecture

## Overview

Tongy-Agent is a modular AI Agent framework powered by Zhipu GLM-4.7. It provides a complete solution for building intelligent programming assistants with file operations, tool execution, memory management, and security controls.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                            CLI                                  │
│  (Interactive command-line interface with rich output)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Agent                                 │
│  (Core orchestration, conversation management, tool execution)  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      LLM        │  │     Tools       │  │    Memory       │
│   (GLM-4.7)     │  │  (File, Bash,   │  │  (Repository    │
│                 │  │   TODO, MCP)    │  │   Persistence)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Sandbox                                 │
│      (File access control, command execution security)          │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent (`tongy_agent/agent.py`)

The Agent class is the core orchestrator that:
- Manages conversation history
- Calls the LLM API
- Executes tools
- Handles context summarization
- Coordinates all other components

**Key Methods:**
- `run()`: Main execution loop
- `add_user_message()`: Add user input
- `_call_llm()`: Invoke the LLM
- `_execute_tools()`: Run requested tools

### 2. LLM Layer (`tongy_agent/llm/`)

Provides abstraction over LLM APIs:
- `LLMClientBase`: Abstract base class
- `GLMClient`: Zhipu GLM-4.7 implementation
- Retry logic and error handling

### 3. Tools System (`tongy_agent/tools/`)

Modular tool system with:
- **Base Tool**: Abstract interface for all tools
- **File Tools**: Read, Write, Edit, List directory
- **Bash Tool**: Execute shell commands with safety controls
- **TODO Tool**: Task tracking and management
- **MCP Loader**: Load MCP servers
- **Skill Loader**: Load Claude Skills

### 4. Sandbox (`tongy_agent/sandbox.py`)

Security layer providing:
- **FileSandbox**: Path-based access control
- **CommandSandbox**: Command execution filtering
- **Sandbox**: Combined security interface

### 5. Memory (`tongy_agent/memory.py`)

Repository-level persistence:
- Stores memories in JSON format
- Category-based organization
- Search and retrieval
- Context prompt generation

### 6. Logger (`tongy_agent/logger.py`)

Detailed logging and tracing:
- Request/response logging
- Tool execution tracking
- Error capture
- JSONL trace files

### 7. SubAgent System (`tongy_agent/subagent/`)

Task delegation framework:
- **SubAgent**: Specialized agent base class
- **SubAgentManager**: Registry and delegation
- **Predefined Agents**: Code, Research, Testing

### 8. Configuration (`tongy_agent/config.py`)

Flexible configuration management:
- YAML file support
- Environment variable overrides
- Validation and defaults

## Data Flow

### Request Flow
```
User Input → CLI → Agent.add_user_message()
         ↓
Agent.run() → Agent._call_llm()
         ↓
LLM generates response with/without tool calls
         ↓
If tool calls: Agent._execute_tools() → Tool.execute()
         ↓
Tool results added to conversation
         ↓
Repeat until done or max_steps reached
```

### Memory Flow
```
Agent initialization → RepositoryMemory.load()
         ↓
During run: memory.add(), memory.search()
         ↓
Context generation → memory.get_context_prompt()
         ↓
Injected into system prompt
```

## Security Model

### File Access
- **Allowed Paths**: Whitelist of permitted directories
- **Forbidden Paths**: Blacklist of restricted directories
- **File Size Limits**: Maximum file size for reading

### Command Execution
- **Allowed Commands**: Explicitly permitted commands
- **Forbidden Commands**: Dangerous commands blocked by default
- **Sandboxing**: Commands run in controlled environment

## Extension Points

### Custom Tools
```python
from tongy_agent.tools.base import Tool

class MyTool(Tool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "My custom tool"

    @property
    def parameters(self) -> dict:
        return {"type": "object", ...}

    async def execute(self, **kwargs) -> ToolResult:
        # Implementation
        return ToolResult(success=True, content="...")
```

### Custom SubAgents
```python
from tongy_agent.subagent.base import SubAgent

class MySubAgent(SubAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="my_agent",
            description="My specialized agent",
            **kwargs
        )
```

## Configuration Priority

1. Explicit `config_path` parameter
2. Default search paths:
   - `./tongy_agent/config/config.yaml`
   - `~/.tongy-agent/config/config.yaml`
   - `~/.config/tongy-agent/config.yaml`
3. Environment variables (override)
4. Built-in defaults

## Dependencies

- **pydantic**: Data validation and serialization
- **httpx**: Async HTTP client for LLM API
- **pyyaml**: Configuration file parsing
- **prompt-toolkit**: Interactive CLI
- **rich**: Terminal formatting
- **tiktoken**: Token estimation

## Future Enhancements

- Streaming responses
- Multi-modal content support
- Advanced memory retrieval (semantic search)
- Tool composition
- Distributed execution
- Web UI
