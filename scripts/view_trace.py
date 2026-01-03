#!/usr/bin/env python3
"""
HTTP Trace Viewer for Tongy-Agent.

View and analyze HTTP communication logs.
"""

import argparse
import json
import sys
from pathlib import Path


def view_trace_file(trace_file: str, show_full: bool = False):
    """
    View a trace file.

    Args:
        trace_file: Path to trace file
        show_full: Show full content (not truncated)
    """
    trace_path = Path(trace_file)

    if not trace_path.exists():
        print(f"Error: Trace file not found: {trace_file}")
        sys.exit(1)

    print(f"Reading trace from: {trace_path}\n")

    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                print_event(event, show_full)
                print("-" * 80)
            except json.JSONDecodeError as e:
                print(f"Error parsing line: {e}")
                print(f"Raw line: {line[:100]}...")


def print_event(event: dict, show_full: bool = False):
    """Print a single event."""
    event_type = event.get("type", "unknown")
    timestamp = event.get("timestamp", "")
    request_id = event.get("request_id", "?")

    if event_type == "http_request":
        data = event.get("data", {})
        print(f"📤 [Request #{request_id}] {timestamp}")
        print(f"   Method: {data.get('method')}")
        print(f"   URL: {data.get('url')}")

        headers = data.get("headers", {})
        if headers:
            print(f"   Headers:")
            for key, value in headers.items():
                print(f"     {key}: {value}")

        body = data.get("body")
        if body:
            print(f"   Body:")
            body_str = json.dumps(body, indent=2, ensure_ascii=False)
            if not show_full and len(body_str) > 500:
                body_str = body_str[:500] + "\n   ... (truncated)"
            for line in body_str.split("\n"):
                print(f"     {line}")

    elif event_type == "http_response":
        data = event.get("data", {})
        status_code = data.get("status_code", "?")
        duration = data.get("duration_ms")

        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        duration_str = f" ({duration:.0f}ms)" if duration else ""

        print(f"📥 [Response #{request_id}] {status_emoji} {status_code}{duration_str}")

        headers = data.get("headers")
        if headers and show_full:
            print(f"   Headers:")
            for key, value in headers.items():
                print(f"     {key}: {value}")

        body = data.get("body")
        if body:
            print(f"   Body:")
            if "choices" in body:
                choices = body.get("choices", [])
                if choices:
                    choice = choices[0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    tool_calls = message.get("tool_calls")

                    if content:
                        content_preview = content[:200] + "..." if len(content) > 200 else content
                        print(f"     Content: {content_preview}")

                    if tool_calls:
                        print(f"     Tool Calls:")
                        for tc in tool_calls:
                            func = tc.get("function", {})
                            print(f"       - {func.get('name')}: {func.get('arguments', {})}")

            if "usage" in body and show_full:
                usage = body.get("usage", {})
                print(f"   Usage:")
                print(f"     - Prompt tokens: {usage.get('prompt_tokens')}")
                print(f"     - Completion tokens: {usage.get('completion_tokens')}")
                print(f"     - Total tokens: {usage.get('total_tokens')}")

    elif event_type == "http_error":
        data = event.get("data", {})
        print(f"❌ [Error #{request_id}] {timestamp}")
        print(f"   Error: {data.get('error')}")
        if data.get("exception_type"):
            print(f"   Type: {data.get('exception_type')}")
        if data.get("traceback") and show_full:
            print(f"   Traceback:")
            for line in data.get("traceback", "").split("\n"):
                print(f"     {line}")


def list_sessions():
    """List all available trace sessions."""
    trace_dir = Path.home() / ".tongy-agent" / "traces"

    if not trace_dir.exists():
        print("No trace directory found")
        return

    trace_files = sorted(trace_dir.glob("session_*.jsonl"), reverse=True)

    if not trace_files:
        print("No trace sessions found")
        return

    print(f"Available trace sessions in {trace_dir}:\n")

    for trace_file in trace_files:
        # Get session info
        request_count = 0
        try:
            with open(trace_file, "r") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get("type") == "http_request":
                            request_count += 1
        except:
            pass

        # Extract session ID from filename
        session_id = trace_file.stem.replace("session_", "")
        print(f"  📁 {trace_file.name}")
        print(f"     Session: {session_id}")
        print(f"     Requests: {request_count}")
        print(f"     Path: {trace_file}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="View HTTP traces from Tongy-Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available trace sessions
  python scripts/view_trace.py --list

  # View a specific trace file
  python scripts/view_trace.py ~/.tongy-agent/traces/session_20240103_152206.jsonl

  # View with full content
  python scripts/view_trace.py session_20240103_152206.jsonl --full
        """
    )

    parser.add_argument(
        "trace_file",
        nargs="?",
        help="Path to trace file or session ID",
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available trace sessions",
    )

    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Show full content without truncation",
    )

    args = parser.parse_args()

    if args.list:
        list_sessions()
    elif args.trace_file:
        # Handle relative path or session ID
        trace_path = args.trace_file
        if not "/" in trace_path and not trace_path.startswith("~"):
            # Assume it's a session ID, look in default directory
            trace_dir = Path.home() / ".tongy-agent" / "traces"
            trace_path = trace_dir / f"session_{trace_path}.jsonl"

        view_trace_file(trace_path, args.full)
    else:
        # Default: list sessions
        list_sessions()


if __name__ == "__main__":
    main()
