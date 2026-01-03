"""
Tongy-Agent: A Claude Code-like AI Agent powered by Zhipu GLM-4.7

This package provides a comprehensive AI Agent framework with:
- GLM-4.7 LLM integration
- File operations with sandbox security
- MCP Server support
- SubAgent system
- Repository-level memory
- Detailed logging and tracing
"""

__version__ = "0.1.0"

from tongy_agent.agent import Agent
from tongy_agent.http_tracer import HTTPTracer, get_tracer
from tongy_agent.schema.schema import (
    LLMResponse,
    Message,
    ToolCall,
    FunctionCall,
    TokenUsage,
    MemoryItem,
    SandboxConfig,
)

__all__ = [
    "Agent",
    "HTTPTracer",
    "get_tracer",
    "LLMResponse",
    "Message",
    "ToolCall",
    "FunctionCall",
    "TokenUsage",
    "MemoryItem",
    "SandboxConfig",
]
