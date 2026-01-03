"""
HTTP communication tracer for debugging LLM API calls.

Records complete HTTP requests and responses for packet inspection.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class HTTPTracer:
    """
    HTTP tracer for capturing complete LLM API communication.

    Records:
    - Full request headers and body
    - Full response headers and body
    - Timing information
    - Error details
    """

    def __init__(self, trace_dir: str | None = None):
        """
        Initialize the HTTP tracer.

        Args:
            trace_dir: Directory to store trace files
        """
        if trace_dir:
            self.trace_dir = Path(trace_dir)
        else:
            self.trace_dir = Path.home() / ".tongy-agent" / "traces"

        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.trace_dir / f"session_{self.session_id}.jsonl"
        self.request_count = 0

    def log_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
    ):
        """
        Log an HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body (JSON)
        """
        self.request_count += 1

        # Sanitize headers (hide sensitive data)
        safe_headers = self._sanitize_headers(headers)

        event = {
            "type": "http_request",
            "session_id": self.session_id,
            "request_id": self.request_count,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "method": method,
                "url": url,
                "headers": safe_headers,
                "body": body,
            },
        }

        self._write_event(event)

    def log_response(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: Any = None,
        duration_ms: float | None = None,
        error: str | None = None,
    ):
        """
        Log an HTTP response.

        Args:
            status_code: HTTP status code
            headers: Response headers
            body: Response body
            duration_ms: Request duration in milliseconds
            error: Error message if request failed
        """
        event = {
            "type": "http_response",
            "session_id": self.session_id,
            "request_id": self.request_count,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "status_code": status_code,
                "headers": headers,
                "body": body,
                "duration_ms": duration_ms,
                "error": error,
            },
        }

        self._write_event(event)

    def log_error(
        self,
        error: str,
        exception_type: str | None = None,
        traceback: str | None = None,
    ):
        """
        Log an error.

        Args:
            error: Error message
            exception_type: Exception type name
            traceback: Exception traceback
        """
        event = {
            "type": "http_error",
            "session_id": self.session_id,
            "request_id": self.request_count,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "error": error,
                "exception_type": exception_type,
                "traceback": traceback,
            },
        }

        self._write_event(event)

    def _sanitize_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Sanitize headers to hide sensitive information.

        Args:
            headers: Original headers

        Returns:
            Sanitized headers
        """
        safe = {}
        sensitive_keys = {"authorization", "cookie", "set-cookie", "x-api-key"}

        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                # Show first 20 chars of sensitive values
                safe[key] = f"{value[:20]}..." if len(value) > 20 else "***HIDDEN***"
            else:
                safe[key] = value

        return safe

    def _write_event(self, event: dict[str, Any]):
        """Write an event to the trace file."""
        try:
            with open(self.session_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error writing trace: {e}")

    def get_session_file(self) -> Path:
        """Get the current session trace file path."""
        return self.session_file

    def get_summary(self) -> str:
        """
        Get a summary of the traced session.

        Returns:
            Summary string
        """
        lines = [
            f"HTTP Trace Session: {self.session_id}",
            f"Total requests: {self.request_count}",
            f"Trace file: {self.session_file}",
        ]
        return "\n".join(lines)


# Global tracer instance
_tracer: HTTPTracer | None = None


def get_tracer() -> HTTPTracer:
    """Get the global HTTP tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = HTTPTracer()
    return _tracer


def reset_tracer():
    """Reset the global HTTP tracer."""
    global _tracer
    _tracer = None
