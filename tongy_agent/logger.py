"""
Logging system for Tongy-Agent.

Provides detailed logging and tracing for debugging agent behavior.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from tongy_agent.schema.schema import Message, ToolCall

# Configure root logger with console and file handlers
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Console handler - only INFO and above
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(console_formatter)

# Add console handler to root logger
root_logger.addHandler(console_handler)

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class AgentLogger:
    """
    Agent-specific logger with detailed tracing capabilities.

    Logs all interactions between the agent and LLM, including:
    - Request messages and tools
    - Response content and tool calls
    - Tool execution results
    - Errors and exceptions
    """

    def __init__(
        self,
        log_dir: str | None = None,
        verbose: bool = False,
        enable_trace: bool = True,
    ):
        """
        Initialize the agent logger.

        Args:
            log_dir: Directory to store log files
            verbose: Whether to enable verbose logging
            enable_trace: Whether to enable detailed trace logging
        """
        self.verbose = verbose
        self.enable_trace = enable_trace

        # Setup log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".tongy-agent" / "logs"

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current run log
        self.current_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_log_file = self.log_dir / f"run_{self.current_run_id}.jsonl"
        self.events: list[dict[str, Any]] = []

        if self.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def start_new_run(self):
        """Start a new run with a fresh run ID."""
        self.current_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_log_file = self.log_dir / f"run_{self.current_run_id}.jsonl"
        self.events.clear()
        logger.info(f"Starting new run: {self.current_run_id}")

    def log_request(
        self,
        messages: list[Message],
        tools: list[Any],
    ):
        """
        Log an LLM request.

        Args:
            messages: List of messages being sent
            tools: List of available tools
        """
        event = {
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "run_id": self.current_run_id,
            "data": {
                "message_count": len(messages),
                "tool_count": len(tools),
                "messages": self._serialize_messages(messages),
                "tools": [tool.name for tool in tools],
            },
        }

        self.events.append(event)
        logger.debug(f"LLM Request: {len(messages)} messages, {len(tools)} tools")

        if self.enable_trace:
            self._write_event(event)

    def log_response(
        self,
        content: str,
        tool_calls: list[ToolCall] | None,
        finish_reason: str,
    ):
        """
        Log an LLM response.

        Args:
            content: Response content
            tool_calls: Tool calls requested
            finish_reason: Reason for finishing
        """
        event = {
            "type": "response",
            "timestamp": datetime.now().isoformat(),
            "run_id": self.current_run_id,
            "data": {
                "content": content[:1000] + "..." if len(content) > 1000 else content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.function.name}
                    for tc in (tool_calls or [])
                ],
                "finish_reason": finish_reason,
            },
        }

        self.events.append(event)
        logger.debug(f"LLM Response: finish_reason={finish_reason}, tool_calls={len(tool_calls or [])}")

        if self.enable_trace:
            self._write_event(event)

    def log_tool_result(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result_success: bool,
        result_content: str | None = None,
        result_error: str | None = None,
    ):
        """
        Log a tool execution result.

        Args:
            tool_name: Name of the tool
            arguments: Arguments passed to the tool
            result_success: Whether the tool execution was successful
            result_content: Output content if successful
            result_error: Error message if failed
        """
        event = {
            "type": "tool_result",
            "timestamp": datetime.now().isoformat(),
            "run_id": self.current_run_id,
            "data": {
                "tool_name": tool_name,
                "arguments": arguments,
                "success": result_success,
                "content": (result_content or "")[:1000] if result_success else None,
                "error": result_error if not result_success else None,
            },
        }

        self.events.append(event)
        status = "✓" if result_success else "✗"
        logger.debug(f"Tool {status} {tool_name}")

        if self.enable_trace:
            self._write_event(event)

    def log_error(self, error: str, exception: Exception | None = None):
        """
        Log an error.

        Args:
            error: Error message
            exception: Optional exception object
        """
        event = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "run_id": self.current_run_id,
            "data": {
                "error": error,
                "exception_type": type(exception).__name__ if exception else None,
            },
        }

        self.events.append(event)
        logger.error(f"Error: {error}")

        if self.enable_trace:
            self._write_event(event)

    def log_info(self, message: str):
        """Log an info message."""
        event = {
            "type": "info",
            "timestamp": datetime.now().isoformat(),
            "run_id": self.current_run_id,
            "data": {"message": message},
        }

        self.events.append(event)
        logger.info(message)

        if self.enable_trace:
            self._write_event(event)

    def _write_event(self, event: dict[str, Any]):
        """Write an event to the trace log file."""
        try:
            with open(self.run_log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Error writing trace log: {e}")

    def _serialize_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Serialize messages for logging."""
        serialized = []
        for msg in messages:
            msg_dict = {
                "role": msg.role,
                "content": str(msg.content)[:500],  # Truncate long content
            }
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {"id": tc.id, "name": tc.function.name}
                    for tc in msg.tool_calls
                ]
            serialized.append(msg_dict)
        return serialized

    def save_trace(self, filename: str | None = None):
        """
        Save the complete trace to a file.

        Args:
            filename: Optional filename (default: run_<timestamp>.json)
        """
        if filename is None:
            filename = f"trace_{self.current_run_id}.json"

        trace_file = self.log_dir / filename

        trace_data = {
            "run_id": self.current_run_id,
            "timestamp": datetime.now().isoformat(),
            "events": self.events,
        }

        try:
            with open(trace_file, "w") as f:
                json.dump(trace_data, f, indent=2)
            logger.info(f"Trace saved to: {trace_file}")
        except Exception as e:
            logger.error(f"Error saving trace: {e}")

    def get_events_summary(self) -> str:
        """
        Get a summary of logged events.

        Returns:
            Summary string
        """
        if not self.events:
            return "No events logged"

        summary = [f"Run ID: {self.current_run_id}\n"]
        summary.append(f"Total events: {len(self.events)}\n")

        # Count by type
        type_counts: dict[str, int] = {}
        for event in self.events:
            event_type = event.get("type", "unknown")
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        summary.append("Event types:")
        for event_type, count in sorted(type_counts.items()):
            summary.append(f"  - {event_type}: {count}")

        return "\n".join(summary)
