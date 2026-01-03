"""
Tests for the LLM client.
"""

import pytest

from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.schema.schema import RetryConfig, Message


class TestGLMClient:
    """Tests for GLMClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return GLMClient(
            api_key="test-key",
            model="glm-4.7",
        )

    def test_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test-key"
        assert client.model == "glm-4.7"
        assert client.api_base == "https://open.bigmodel.cn/api/paas/v4/"

    def test_convert_messages(self, client):
        """Test message conversion."""
        messages = [
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="Hello"),
        ]

        api_messages = client._convert_messages(messages)

        assert len(api_messages) == 2
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"

    def test_convert_messages_with_tools(self, client):
        """Test converting messages with tool calls."""
        from tongy_agent.schema.schema import ToolCall, FunctionCall

        messages = [
            Message(
                role="assistant",
                content="",
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        function=FunctionCall(
                            name="test_tool",
                            arguments={"arg": "value"},
                        ),
                    ),
                ],
            ),
        ]

        api_messages = client._convert_messages(messages)

        assert len(api_messages) == 1
        assert "tool_calls" in api_messages[0]
        assert len(api_messages[0]["tool_calls"]) == 1

    def test_convert_tools_to_schema(self, client):
        """Test tool schema conversion."""
        from tongy_agent.tools.base import Tool

        class MockTool(Tool):
            @property
            def name(self) -> str:
                return "mock_tool"

            @property
            def description(self) -> str:
                return "A mock tool"

            @property
            def parameters(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string"},
                    },
                }

            async def execute(self, **kwargs):
                from tongy_agent.schema.schema import ToolResult
                return ToolResult(success=True, content="done")

        tool = MockTool()
        schemas = client._convert_tools_to_schema([tool])

        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "mock_tool"


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.enabled == True
        assert config.max_retries == 3
        assert config.initial_delay == 1.0

    def test_get_delay(self):
        """Test delay calculation."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
        )

        # Exponential backoff
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        # Should cap at max_delay
        assert config.get_delay(10) == 10.0

    def test_disabled_retry(self):
        """Test disabled retry."""
        config = RetryConfig(enabled=False)

        assert config.enabled == False
        assert config.get_delay(5) == 1.0  # Still calculates delay
