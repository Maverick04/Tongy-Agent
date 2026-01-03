"""
Command-line interface for Tongy-Agent.

Provides an interactive CLI for running the agent.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from tongy_agent.agent import Agent
from tongy_agent.config import ConfigManager
from tongy_agent.llm.glm_client import GLMClient
from tongy_agent.memory import RepositoryMemory
from tongy_agent.sandbox import Sandbox
from tongy_agent.tools.bash_tool import BashTool
from tongy_agent.tools.file_tools import (
    EditFileTool,
    ListDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)
from tongy_agent.tools.todo_tool import TodoWriteTool

console = Console()
logger = logging.getLogger(__name__)


# CLI styling
STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
    "response": "ansigreen",
    "error": "ansired bold",
    "info": "ansiyellow",
})


class TongyAgentCLI:
    """Interactive CLI for Tongy-Agent."""

    def __init__(self, config_path: str | None = None, workspace: str | None = None):
        """
        Initialize the CLI.

        Args:
            config_path: Optional path to configuration file
            workspace: Optional workspace directory override
        """
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Override workspace if specified
        if workspace:
            self.config.agent.workspace_dir = workspace

        # Validate configuration
        errors = self.config_manager.validate()
        if errors:
            for error in errors:
                console.print(f"[error]Configuration error: {error}[/error]")
            sys.exit(1)

        # Initialize components
        self._init_components()

        # Setup prompt session
        self.history = FileHistory(Path.home() / ".tongy-agent" / "history")
        self.session = PromptSession(history=self.history)

        # Commands completer
        self.commands = ["/help", "/quit", "/exit", "/clear", "/config", "/workspace", "/todos"]
        self.completer = WordCompleter(self.commands, ignore_case=True)

    def _init_components(self):
        """Initialize agent components."""
        # Initialize LLM client
        self.llm_client = GLMClient(
            api_key=self.config.llm.api_key,
            api_base=self.config.llm.api_base,
            model=self.config.llm.model,
            retry_config=self.config.llm.retry,
            timeout=self.config.llm.timeout,
        )

        # Initialize sandbox
        self.sandbox = None
        if self.config.agent.enable_sandbox:
            self.sandbox = Sandbox(self.config.sandbox)
            self.sandbox.configure_from_workspace(self.config.agent.workspace_dir)

        # Initialize memory
        self.memory = None
        if self.config.agent.enable_memory:
            self.memory = RepositoryMemory(self.config.agent.workspace_dir)

        # Initialize tools
        self.tools = self._create_tools()

        # Load system prompt
        system_prompt = self.config_manager.get_system_prompt()

        # Initialize agent
        self.agent = Agent(
            llm_client=self.llm_client,
            system_prompt=system_prompt,
            tools=self.tools,
            max_steps=self.config.agent.max_steps,
            workspace_dir=self.config.agent.workspace_dir,
            token_limit=self.config.agent.token_limit,
            memory=self.memory,
            sandbox=self.sandbox,
            verbose=self.config.agent.verbose,
            display_output=True,  # Enable Agent to display responses and tool calls
            interactive=True,  # Enable step-by-step confirmation
        )

    def _create_tools(self) -> list[Any]:
        """Create the tool list."""
        workspace = self.config.agent.workspace_dir
        tools = [
            ReadFileTool(sandbox=self.sandbox, workspace_dir=workspace),
            WriteFileTool(sandbox=self.sandbox, workspace_dir=workspace),
            EditFileTool(sandbox=self.sandbox, workspace_dir=workspace),
            ListDirectoryTool(sandbox=self.sandbox, workspace_dir=workspace),
            BashTool(sandbox=self.sandbox, cwd=workspace),
            TodoWriteTool(workspace_dir=workspace),
        ]

        return tools

    def print_welcome(self):
        """Print welcome message."""
        welcome_text = f"""
[bold cyan]Welcome to Tongy-Agent[/bold cyan]

Model: {self.config.llm.model}
Workspace: {self.config.agent.workspace_dir}

Type [bold]/help[/bold] for commands, [bold]/quit[/bold] to exit.
"""
        console.print(Panel(welcome_text.strip(), border_style="cyan"))

    def print_help(self):
        """Print help information."""
        help_text = """
[bold]Commands:[/bold]
  /help      - Show this help message
  /quit      - Exit Tongy-Agent
  /exit      - Exit Tongy-Agent
  /clear     - Clear the screen
  /config    - Show current configuration
  /workspace - Show workspace information
  /todos     - Show current TODOs

[bold]Usage:[/bold]
  Simply type your request and press Enter.
  The agent will use available tools to help you.
"""
        console.print(Panel(help_text.strip(), title="Help", border_style="cyan"))

    def print_config(self):
        """Print current configuration."""
        config_text = f"""
[bold]LLM Configuration:[/bold]
  Provider: {self.config.llm.provider}
  Model: {self.config.llm.model}
  API Base: {self.config.llm.api_base}
  Max Tokens: {self.config.llm.max_tokens}

[bold]Agent Configuration:[/bold]
  Max Steps: {self.config.agent.max_steps}
  Token Limit: {self.config.agent.token_limit}
  Workspace: {self.config.agent.workspace_dir}
  Memory: {'Enabled' if self.config.agent.enable_memory else 'Disabled'}
  Sandbox: {'Enabled' if self.config.agent.enable_sandbox else 'Disabled'}
  Verbose: {'Enabled' if self.config.agent.verbose else 'Disabled'}
"""
        console.print(Panel(config_text.strip(), title="Configuration", border_style="cyan"))

    def print_workspace(self):
        """Print workspace information."""
        workspace = Path(self.config.agent.workspace_dir).expanduser()

        info_lines = [
            f"[bold]Workspace:[/bold] {workspace}",
            "",
            f"[bold]Exists:[/bold] {workspace.exists()}",
        ]

        if workspace.exists():
            info_lines.append(f"[bold]Files:[/bold]")

            # List files in workspace
            try:
                for item in sorted(workspace.iterdir())[:20]:
                    marker = "DIR" if item.is_dir() else "FILE"
                    info_lines.append(f"  [{marker}] {item.name}")

                if len(list(workspace.iterdir())) > 20:
                    info_lines.append("  ... (more files)")
            except Exception as e:
                info_lines.append(f"  Error: {e}")

        console.print(Panel("\n".join(info_lines), title="Workspace", border_style="cyan"))

    def print_todos(self):
        """Print current TODOs."""
        todo_tool = next((t for t in self.tools if isinstance(t, TodoWriteTool)), None)

        if not todo_tool:
            console.print("[error]TODO tool not available[/error]")
            return

        todos = todo_tool.get_todos()
        summary = todo_tool.get_summary()

        if not todos:
            console.print("[info]No tasks tracked[/info]")
            return

        console.print(Panel(summary, title="TODOs", border_style="cyan"))

    async def run_interactive(self):
        """Run the interactive CLI loop."""
        self.print_welcome()

        try:
            while True:
                try:
                    # Get user input
                    user_input = await self.session.prompt_async(
                        ">>> ",
                        style=STYLE,
                        completer=self.completer,
                    )

                    if not user_input.strip():
                        continue

                    # Handle commands
                    if user_input.startswith("/"):
                        should_exit = await self.handle_command(user_input)
                        if should_exit:
                            break
                        continue

                    # Run agent
                    console.print()  # Blank line for separation

                    self.agent.add_user_message(user_input)
                    response = await self.agent.run()

                    console.print()  # Blank line for separation

                except KeyboardInterrupt:
                    console.print("\n[info]Interrupted. Type /quit to exit.[/info]")
                except EOFError:
                    break
                except Exception as e:
                    console.print(f"[error]Error: {e}[/error]")
                    logger.exception("Unexpected error in CLI loop")

        finally:
            # Always close the LLM client
            await self.llm_client.close()

    async def handle_command(self, command: str) -> bool:
        """
        Handle a CLI command.

        Returns:
            True if the CLI should exit, False otherwise
        """
        cmd = command.strip().lower()

        if cmd in ("/quit", "/exit"):
            console.print("[info]Goodbye![/info]")
            return True
        elif cmd == "/help":
            self.print_help()
        elif cmd == "/clear":
            import os
            os.system("clear" if os.name != "nt" else "cls")
        elif cmd == "/config":
            self.print_config()
        elif cmd == "/workspace":
            self.print_workspace()
        elif cmd == "/todos":
            self.print_todos()
        else:
            console.print(f"[error]Unknown command: {command}[/error]")
            console.print("Type /help for available commands")

        return False

    def display_response(self, response: str):
        """Display agent response with formatting."""
        # Check if response contains code blocks
        if "```" in response:
            # Display as markdown
            md = Markdown(response)
            console.print(md)
        else:
            # Display as plain text with some formatting
            console.print(Panel(response.strip(), border_style="green"))


def main():
    """Main entry point for the CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Tongy-Agent - AI Programming Assistant")
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--workspace", "-w",
        help="Workspace directory",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Initialize example configuration file",
    )

    args = parser.parse_args()

    # Handle init-config
    if args.init_config:
        manager = ConfigManager()
        config_path = Path("./tongy_agent/config/config-example.yaml")
        manager.save_example_config(config_path)
        console.print(f"[info]Example configuration saved to: {config_path}[/info]")
        console.print("[info]Edit this file and set TONGY_API_KEY environment variable.[/info]")
        return

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run CLI
    cli = TongyAgentCLI(config_path=args.config, workspace=args.workspace)

    try:
        asyncio.run(cli.run_interactive())
    except KeyboardInterrupt:
        console.print("\n[info]Goodbye![/info]")


if __name__ == "__main__":
    main()
