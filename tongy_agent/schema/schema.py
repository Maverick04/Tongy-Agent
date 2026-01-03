"""
Core data models for Tongy-Agent.

This module defines all Pydantic models used throughout the agent system,
ensuring type safety and data validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ZHIPU = "zhipu"  # Zhipu AI (GLM-4.7)


class FunctionCall(BaseModel):
    """Represents a function call from the LLM."""

    name: str = Field(description="Name of the function to call")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments for the function")


class ToolCall(BaseModel):
    """Represents a tool call from the LLM."""

    id: str = Field(description="Unique identifier for this tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: FunctionCall = Field(description="Function call details")


class Message(BaseModel):
    """
    Represents a message in the conversation.

    Supports both text content and multimodal content (images, etc.).
    """

    role: str = Field(description="Message role: system, user, assistant, or tool")
    content: str | list[dict[str, Any]] = Field(description="Message content")
    tool_calls: list[ToolCall] | None = Field(default=None, description="Tool calls from assistant")
    tool_call_id: str | None = Field(default=None, description="Tool call ID for tool responses")
    name: str | None = Field(default=None, description="Name of the tool that was called")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class TokenUsage(BaseModel):
    """Token usage statistics for an LLM request."""

    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(default=0, description="Number of tokens in the completion")
    total_tokens: int = Field(default=0, description="Total number of tokens used")

    @classmethod
    def from_glm_usage(cls, usage: dict[str, Any]) -> "TokenUsage":
        """Create TokenUsage from GLM API usage format."""
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )


class LLMResponse(BaseModel):
    """Represents a response from the LLM."""

    content: str = Field(description="Text content of the response")
    tool_calls: list[ToolCall] | None = Field(default=None, description="Tool calls requested by LLM")
    finish_reason: str = Field(description="Reason for finishing (stop, tool_calls, length, etc.)")
    usage: TokenUsage | None = Field(default=None, description="Token usage statistics")


class ToolResult(BaseModel):
    """
    Result of a tool execution.

    Contains either successful output or error information.
    """

    success: bool = Field(description="Whether the tool execution was successful")
    content: str = Field(default="", description="Output content if successful")
    error: str | None = Field(default=None, description="Error message if failed")


class MemoryItem(BaseModel):
    """
    A single memory item stored in the repository memory.

    Memories are persisted across sessions and provide context for the agent.
    """

    key: str = Field(description="Identifier or title for this memory")
    value: str = Field(description="The actual memory content")
    category: str = Field(default="general", description="Category for organizing memories")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When this memory was created")
    repository: str = Field(description="Repository path for scoping")


class SandboxConfig(BaseModel):
    """
    Configuration for the sandbox security system.

    Controls what files and commands the agent can access.
    """

    # File access control
    allowed_paths: list[str] = Field(
        default_factory=list, description="Paths where file access is allowed"
    )
    forbidden_paths: list[str] = Field(
        default_factory=list, description="Paths where file access is forbidden"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size in bytes (default 10MB)"
    )

    # Command execution control
    allowed_commands: list[str] = Field(
        default_factory=list, description="Commands that are allowed to execute"
    )
    forbidden_commands: list[str] = Field(
        default_factory=[
            "rm",
            "rmdir",
            "del",
            "format",
            "mkfs",
            "dd",
            "shutdown",
            "reboot",
            "halt",
        ],
        description="Commands that are forbidden to execute",
    )

    # Network control
    allow_network_access: bool = Field(
        default=False, description="Whether network access is allowed"
    )


class RetryConfig(BaseModel):
    """Configuration for retry logic."""

    enabled: bool = Field(default=True, description="Whether retry is enabled")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    initial_delay: float = Field(default=1.0, description="Initial delay in seconds")
    max_delay: float = Field(default=10.0, description="Maximum delay in seconds")
    exponential_base: float = Field(default=2.0, description="Base for exponential backoff")

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class LLMConfig(BaseModel):
    """Configuration for LLM client."""

    provider: LLMProvider = Field(default=LLMProvider.ZHIPU, description="LLM provider")
    api_key: str = Field(description="API key for the LLM provider")
    api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4/", description="Base URL for API"
    )
    model: str = Field(default="glm-4.7", description="Model name to use")
    timeout: int = Field(default=120, description="Request timeout in seconds")
    max_tokens: int = Field(default=16384, description="Maximum tokens in response")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")


class AgentConfig(BaseModel):
    """Configuration for the Agent."""

    max_steps: int = Field(default=50, description="Maximum number of agent steps")
    token_limit: int = Field(default=80000, description="Token limit for context management")
    workspace_dir: str = Field(default="./workspace", description="Workspace directory path")
    enable_memory: bool = Field(default=True, description="Whether memory is enabled")
    enable_sandbox: bool = Field(default=True, description="Whether sandbox is enabled")
    verbose: bool = Field(default=False, description="Whether verbose logging is enabled")


class ToolsConfig(BaseModel):
    """Configuration for tools."""

    enable_mcp: bool = Field(default=True, description="Whether MCP tools are enabled")
    enable_skills: bool = Field(default=True, description="Whether Skills are enabled")
    mcp_servers: list[dict[str, Any]] = Field(
        default_factory=list, description="List of MCP servers to connect to"
    )
    skills_path: str | None = Field(
        default=None, description="Path to Claude Skills directory"
    )


class Config(BaseModel):
    """Root configuration for Tongy-Agent."""

    llm: LLMConfig = Field(description="LLM configuration")
    agent: AgentConfig = Field(default_factory=AgentConfig, description="Agent configuration")
    tools: ToolsConfig = Field(default_factory=ToolsConfig, description="Tools configuration")
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig, description="Sandbox configuration")
