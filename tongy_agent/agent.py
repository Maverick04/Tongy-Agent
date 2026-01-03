"""
Agent core implementation for Tongy-Agent.

The main Agent class that orchestrates LLM interactions, tool execution,
and conversation management.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import confirm
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from tongy_agent.llm.base import LLMClientBase
from tongy_agent.logger import AgentLogger
from tongy_agent.memory import RepositoryMemory
from tongy_agent.sandbox import Sandbox
from tongy_agent.schema.schema import LLMResponse, Message, ToolCall, ToolResult
from tongy_agent.tools.base import Tool

logger = logging.getLogger(__name__)
console = Console()
prompt_session = PromptSession()


class Agent:
    """
    Core Agent implementation for Tongy-Agent.

    Manages the conversation loop, tool execution, and context management.
    """

    def __init__(
        self,
        llm_client: LLMClientBase,
        system_prompt: str,
        tools: list[Tool],
        max_steps: int = 50,
        workspace_dir: str = "./workspace",
        token_limit: int = 80000,
        memory: RepositoryMemory | None = None,
        sandbox: Sandbox | None = None,
        verbose: bool = False,
        display_output: bool = True,
        interactive: bool = True,
    ):
        """
        Initialize the Agent.

        Args:
            llm_client: LLM client for generating responses
            system_prompt: System prompt for the agent
            tools: List of available tools
            max_steps: Maximum number of steps before stopping
            workspace_dir: Workspace directory path
            token_limit: Token limit for context management
            memory: Optional repository memory system
            sandbox: Optional sandbox for security
            verbose: Enable verbose logging
            display_output: Display responses and tool calls to console
            interactive: Require user confirmation after each step
        """
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.token_limit = token_limit
        self.workspace_dir = Path(workspace_dir).absolute()
        self.memory = memory
        self.sandbox = sandbox
        self.verbose = verbose
        self.display_output = display_output
        self.interactive = interactive

        # Initialize logger
        self.logger = AgentLogger(verbose=verbose)

        # Build system prompt with context
        self.system_prompt = self._build_system_prompt(system_prompt)

        # Initialize message history
        self.messages: list[Message] = [
            Message(role="system", content=self.system_prompt)
        ]

        # Token tracking
        self.api_total_tokens: int = 0
        self._skip_next_token_check: bool = False

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build the complete system prompt with context."""
        prompt_parts = [base_prompt]

        # Add workspace information
        prompt_parts.append(f"\n## Current Workspace\n{self.workspace_dir}")

        # Add memory context if available
        if self.memory:
            memory_context = self.memory.get_context_prompt()
            if memory_context:
                prompt_parts.append(f"\n{memory_context}")

        # Add tool information
        if self.tools:
            prompt_parts.append("\n## Available Tools\n")
            for tool_name in sorted(self.tools.keys()):
                tool = self.tools[tool_name]
                prompt_parts.append(f"- {tool_name}: {tool.description}")

        return "\n".join(prompt_parts)

    def add_user_message(self, content: str):
        """
        Add a user message to the conversation.

        Args:
            content: Message content
        """
        self.messages.append(Message(role="user", content=content))
        self.logger.log_info(f"User message: {content[:100]}...")

    def add_system_message(self, content: str):
        """
        Add a system message to the conversation.

        Args:
            content: Message content
        """
        self.messages.append(Message(role="system", content=content))

    async def run(self) -> str:
        """
        Run the agent loop.

        Executes the main conversation loop:
        1. Check token limit and summarize if needed
        2. Call LLM
        3. Execute any requested tools
        4. Ask user for confirmation (if interactive)
        5. Repeat until done or max_steps reached

        Returns:
            Final response content
        """
        self.logger.start_new_run()

        step = 0
        while step < self.max_steps:
            # Check token limit and summarize if needed
            await self._maybe_summarize_messages()

            # Call LLM
            try:
                response = await self._call_llm()
            except Exception as e:
                self.logger.log_error(f"LLM call failed: {e}", e)
                return f"Error: LLM call failed - {e}"

            # Check if we're done
            if not response.tool_calls:
                # Final response
                self.logger.log_info(f"Agent finished: {response.finish_reason}")
                if self.display_output:
                    console.print(Panel("[green]✓ Task completed successfully![/green]", border_style="green"))
                return response.content

            # Execute tools
            await self._execute_tools(response.tool_calls)

            # Step completed notification
            if self.display_output:
                console.print(Panel(f"[cyan]Step {step + 1} completed[/cyan]", border_style="cyan"))

            # Ask for user confirmation if interactive
            if self.interactive:
                should_continue = await self._ask_continue()
                if not should_continue:
                    if self.display_output:
                        console.print("[yellow]Operation cancelled by user.[/yellow]")
                    return "Operation cancelled by user."

            step += 1

        return f"Task not completed after {self.max_steps} steps"

    async def _call_llm(self) -> LLMResponse:
        """
        Call the LLM API.

        Returns:
            LLM response
        """
        # Prepare tools list
        tool_list = list(self.tools.values())

        # Log request
        self.logger.log_request(self.messages, tool_list)

        # Call LLM
        try:
            response = await self.llm.generate(
                messages=self.messages,
                tools=tool_list,
            )
        except Exception as e:
            self.logger.log_error(str(e), e)
            raise

        # Track token usage
        if response.usage:
            self.api_total_tokens += response.usage.total_tokens
            self.logger.log_info(f"Tokens: {response.usage.total_tokens} (total: {self.api_total_tokens})")

        # Log response
        self.logger.log_response(
            content=response.content,
            tool_calls=response.tool_calls,
            finish_reason=response.finish_reason,
        )

        # Display response content to user
        if self.display_output and response.content:
            console.print(Panel(Markdown(response.content), title="Assistant", border_style="blue"))

        # Add assistant message
        self.messages.append(Message(
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls,
        ))

        return response

    async def _execute_tools(self, tool_calls: list[ToolCall]):
        """
        Execute requested tools.

        Args:
            tool_calls: List of tool calls to execute
        """
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            # Display tool call to user
            if self.display_output:
                args_str = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
                console.print(f"[cyan]🔧 Calling:[/cyan] {tool_name}({args_str})")

            # Check if tool exists
            if tool_name not in self.tools:
                result = ToolResult(
                    success=False,
                    content="",
                    error=f"Unknown tool: {tool_name}",
                )
                self._add_tool_result(tool_call, tool_name, result)
                if self.display_output:
                    console.print(f"[red]❌ Error: {result.error}[/red]")
                continue

            # Get tool
            tool = self.tools[tool_name]

            # Execute tool
            try:
                result = await tool.execute(**arguments)
            except Exception as e:
                self.logger.log_error(f"Tool {tool_name} failed: {e}", e)
                result = ToolResult(
                    success=False,
                    content="",
                    error=str(e),
                )

            # Display tool result
            if self.display_output:
                if result.success:
                    # Special handling for edit_file with diff output
                    if tool_name == "edit_file" and "---" in result.content:
                        parts = result.content.split("\n\n---\n", 1)
                        summary = parts[0]
                        console.print(f"[green]✓ {summary}[/green]")
                        if len(parts) > 1:
                            diff_content = parts[1]
                            # Display diff in a panel with syntax highlighting
                            console.print(Panel(
                                Syntax(diff_content, "diff", theme="monokai"),
                                title="Diff",
                                border_style="cyan",
                                padding=(0, 0)
                            ))
                    else:
                        # Show truncated result for other tools
                        result_preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                        console.print(f"[green]✓ Result:[/green] {result_preview}")
                else:
                    console.print(f"[red]❌ Error:[/red] {result.error}")

            # Log result
            self.logger.log_tool_result(
                tool_name=tool_name,
                arguments=arguments,
                result_success=result.success,
                result_content=result.content if result.success else None,
                result_error=result.error if not result.success else None,
            )

            # Add tool result message
            self._add_tool_result(tool_call, tool_name, result)

    def _add_tool_result(self, tool_call: ToolCall, tool_name: str, result: ToolResult):
        """
        Add a tool result message to the conversation.

        Args:
            tool_call: The original tool call
            tool_name: Name of the tool
            result: Tool execution result
        """
        content = result.content if result.success else f"Error: {result.error}"

        self.messages.append(Message(
            role="tool",
            content=content,
            tool_call_id=tool_call.id,
            name=tool_name,
        ))

    async def _ask_continue(self) -> bool:
        """
        Ask user if they want to continue to the next step.

        Returns:
            True if user wants to continue, False otherwise
        """
        try:
            # Use prompt_toolkit confirm for better UX
            result = await confirm("Continue to next step?")
            return result
        except (KeyboardInterrupt, EOFError):
            # User pressed Ctrl+C or Ctrl+D
            return False
        except Exception as e:
            # Fallback to default behavior
            logger.debug(f"Confirm prompt failed: {e}, continuing")
            return True

    async def _maybe_summarize_messages(self):
        """Summarize messages if approaching token limit."""
        if self._skip_next_token_check:
            self._skip_next_token_check = False
            return

        estimated_tokens = self.llm.estimate_tokens(self.messages)

        if estimated_tokens > self.token_limit:
            self.logger.log_info(f"Token limit approaching: {estimated_tokens}/{self.token_limit}")

            # Summarize old messages
            summarized = await self._summarize_messages()
            if summarized:
                self.logger.log_info(f"Summarized {summarized} messages")

    async def _summarize_messages(self) -> int | None:
        """
        Summarize old messages to reduce context.

        Returns:
            Number of messages that were summarized
        """
        if len(self.messages) <= 3:
            return None

        # Keep system prompt, summarize the rest
        system_msg = self.messages[0]
        old_messages = self.messages[1:-2]  # Keep last 2 messages for context
        recent_messages = self.messages[-2:]

        # Create summary prompt
        summary_prompt = """Summarize the following conversation history into a concise summary
that captures the key information, tasks, and outcomes. Focus on what was accomplished
and what is still pending.

Conversation history:
"""
        for msg in old_messages:
            if msg.role == "user":
                summary_prompt += f"\nUser: {msg.content[:200]}..."
            elif msg.role == "assistant" and msg.content:
                summary_prompt += f"\nAssistant: {msg.content[:200]}..."

        # Call LLM for summary
        try:
            summary_response = await self.llm.generate(
                messages=[Message(role="user", content=summary_prompt)],
                tools=None,
            )

            summary = summary_response.content

            # Rebuild message list with summary
            self.messages = [
                system_msg,
                Message(role="system", content=f"## Previous Conversation Summary\n\n{summary}"),
                *recent_messages,
            ]

            self._skip_next_token_check = True
            return len(old_messages)

        except Exception as e:
            self.logger.log_error(f"Failed to summarize messages: {e}", e)
            return None

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.

        Returns:
            Summary string
        """
        lines = [
            f"Messages: {len(self.messages)}",
            f"Total tokens: {self.api_total_tokens}",
            f"Available tools: {len(self.tools)}",
        ]

        return "\n".join(lines)
