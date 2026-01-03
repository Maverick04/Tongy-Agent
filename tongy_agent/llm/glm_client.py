"""
GLM-4.7 client for Zhipu AI.

Implements the LLM client interface for Zhipu's GLM-4.7 model.
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx

from tongy_agent.http_tracer import get_tracer
from tongy_agent.llm.base import LLMClientBase
from tongy_agent.retry import async_retry
from tongy_agent.schema.schema import LLMResponse, Message, ToolCall, FunctionCall, TokenUsage

logger = logging.getLogger(__name__)


def generate_token(api_key: str, exp_seconds: int = 3600) -> str:
    """
    Generate JWT token for Zhipu AI API.

    Args:
        api_key: API key in format {id}.{secret}
        exp_seconds: Token expiration time in seconds

    Returns:
        JWT token string
    """
    try:
        id, secret = api_key.split(".")
    except ValueError:
        raise ValueError(f"Invalid API key format: {api_key[:10]}...")

    # Header
    header = {
        "alg": "HS256",
        "sign_type": "SIGN",
    }

    # Payload
    timestamp = int(time.time())
    payload = {
        "api_key": id,
        "exp": timestamp + exp_seconds,
        "timestamp": timestamp,
    }

    # Encode header and payload
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=')

    # Signature
    message = f"{header_b64.decode()}.{payload_b64.decode()}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=')

    # JWT token
    token = f"{message}.{signature_b64.decode()}"
    return token


class GLMClient(LLMClientBase):
    """
    Zhipu GLM-4.7 client implementation.

    Uses the GLM-4.7 API via httpx for async HTTP requests.
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://open.bigmodel.cn/api/paas/v4/",
        model: str = "glm-4.7",
        retry_config: Any = None,
        timeout: int = 120,
    ):
        """
        Initialize the GLM client.

        Args:
            api_key: Zhipu AI API key
            api_base: Base URL for the API (default: Zhipu production endpoint)
            model: Model name (default: glm-4.7)
            retry_config: Retry configuration
            timeout: Request timeout in seconds
        """
        super().__init__(api_key, api_base, model, retry_config)
        self.timeout = timeout
        self._token_expiry = 0
        self._current_token = None

        # Initialize async HTTP client (no Authorization header yet)
        self._client = httpx.AsyncClient(
            base_url=api_base,
            headers={
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def _get_token(self) -> str:
        """Get current JWT token, generating a new one if needed."""
        # Check if we need to generate a new token
        if self._current_token is None or time.time() >= self._token_expiry - 60:
            self._current_token = generate_token(self.api_key)
            # Set expiry to 1 hour from now (token is valid for 1 hour)
            self._token_expiry = int(time.time()) + 3600
            logger.debug("Generated new JWT token")

        return self._current_token

    async def _get_headers(self) -> dict[str, str]:
        """Get request headers with current token."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def generate(
        self,
        messages: list[Message],
        tools: list[Any] | None = None,
    ) -> LLMResponse:
        """
        Generate a response from GLM-4.7.

        Args:
            messages: List of messages in the conversation
            tools: List of available tools (for function calling)

        Returns:
            LLMResponse containing the generated content and tool calls

        Raises:
            httpx.HTTPError: If the HTTP request fails
            Exception: If response parsing fails
        """
        api_messages = self._convert_messages(messages)
        api_tools = self._convert_tools_to_schema(tools) if tools else None

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": 16384,
        }

        if api_tools:
            payload["tools"] = api_tools

        # Make API call with retry logic
        if self.retry_config.enabled:
            retry_decorator = async_retry(self.retry_config)
            api_call = retry_decorator(self._make_request)
            response_data = await api_call(payload)
        else:
            response_data = await self._make_request(payload)

        return self._parse_response(response_data)

    async def _make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Make the actual HTTP request to the GLM API.

        Args:
            payload: Request payload

        Returns:
            Parsed JSON response

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        logger.debug(f"GLM API Request: {self.model}")
        logger.debug(f"Messages: {len(payload['messages'])}")

        # Get headers with current token
        headers = await self._get_headers()
        url = f"{self.api_base}chat/completions"

        # Log HTTP request
        tracer = get_tracer()
        tracer.log_request("POST", url, headers, payload)

        # Make request with timing
        start_time = time.time()
        try:
            response = await self._client.post("chat/completions", json=payload, headers=headers)
            duration_ms = (time.time() - start_time) * 1000

            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"GLM API Response: {response_data.get('choices', [{}])[0].get('finish_reason')}")

            # Log HTTP response
            tracer.log_response(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response_data,
                duration_ms=duration_ms,
            )

            return response_data

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            tracer.log_error(str(e), type(e).__name__)
            raise

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """
        Convert Message objects to GLM API format.

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts in GLM API format
        """
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                api_messages.append({
                    "role": "system",
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })
            elif msg.role == "user":
                api_messages.append({
                    "role": "user",
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })
            elif msg.role == "assistant":
                message_dict = {
                    "role": "assistant",
                    "content": msg.content if isinstance(msg.content, str) else "",
                }

                # Add tool_calls if present
                if msg.tool_calls:
                    message_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": json.dumps(tc.function.arguments, ensure_ascii=False),
                            },
                        }
                        for tc in msg.tool_calls
                    ]

                api_messages.append(message_dict)
            elif msg.role == "tool":
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or "",
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })

        return api_messages

    def _convert_tools_to_schema(self, tools: list[Any]) -> list[dict[str, Any]]:
        """
        Convert tool objects to GLM API format.

        GLM uses OpenAI-compatible tool format.

        Args:
            tools: List of tool objects

        Returns:
            List of tool schemas in GLM API format
        """
        if not tools:
            return []

        tool_schemas = []
        for tool in tools:
            if hasattr(tool, "to_schema"):
                schema = tool.to_schema()
                # GLM uses OpenAI format
                if "type" not in schema:
                    schema["type"] = "function"
                tool_schemas.append(schema)
            else:
                # Assume tool has name, description, parameters attributes
                tool_schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                })

        return tool_schemas

    def _parse_response(self, response_data: dict[str, Any]) -> LLMResponse:
        """
        Parse GLM API response into LLMResponse.

        Args:
            response_data: Raw JSON response from GLM API

        Returns:
            Parsed LLMResponse
        """
        choice = response_data["choices"][0]
        message = choice["message"]

        # Parse tool calls
        tool_calls = None
        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = []
            for tc in message["tool_calls"]:
                # Get function info
                func = tc.get("function", {})
                name = func.get("name", "")
                args_raw = func.get("arguments", "{}")

                # Parse arguments - GLM returns them as JSON string
                if isinstance(args_raw, str):
                    try:
                        arguments = json.loads(args_raw)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments: {args_raw}")
                        arguments = {}
                else:
                    arguments = args_raw

                tool_calls.append(ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function=FunctionCall(
                        name=name,
                        arguments=arguments,
                    ),
                ))

            if not tool_calls:
                tool_calls = None

        # Parse usage
        usage = None
        if "usage" in response_data:
            usage = TokenUsage.from_glm_usage(response_data["usage"])

        return LLMResponse(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", "unknown"),
            usage=usage,
        )
