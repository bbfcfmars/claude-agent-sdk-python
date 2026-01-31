#!/usr/bin/env python3
"""
Interactive Terminal UI for Claude Agent SDK.

This example provides a friendly terminal-based interface to interact with Claude,
featuring:
- Clean prompt input with visual styling
- Helpful commands displayed on startup
- Easy-to-use shortcodes
- Colorized output for better readability

Usage:
    python examples/terminal_ui.py

Commands:
    /help     - Show all available commands
    /info     - Show shortcodes and tips
    /clear    - Clear the screen
    /quit     - Exit the session
"""

import asyncio
import os
import sys

# Add src to path for development
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


# ANSI color codes for terminal styling
class Colors:
    """ANSI color codes."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"


def colorize(text: str, *styles: str) -> str:
    """Apply ANSI color codes to text."""
    if not sys.stdout.isatty():
        return text
    return "".join(styles) + text + Colors.RESET


def print_header() -> None:
    """Print the welcome header."""
    header = """
╔═══════════════════════════════════════════════════════════════╗
║         Claude Agent SDK - Interactive Terminal UI            ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(colorize(header, Colors.CYAN, Colors.BOLD))


def print_help() -> None:
    """Print available commands."""
    print()
    print(colorize("📖 Available Commands:", Colors.YELLOW, Colors.BOLD))
    print()

    commands = [
        ("/help", "Show this help message"),
        ("/info", "Show shortcodes and tips"),
        ("/clear", "Clear the terminal screen"),
        ("/quit", "Exit the session"),
        ("/exit", "Exit the session (alias)"),
    ]

    for cmd, desc in commands:
        print(
            f"  {colorize(cmd, Colors.CYAN, Colors.BOLD):20} {colorize(desc, Colors.DIM)}"
        )

    print()


def print_info() -> None:
    """Print shortcodes and tips."""
    print()
    print(colorize("💡 Shortcodes & Tips:", Colors.YELLOW, Colors.BOLD))
    print()

    sections = {
        "Quick Prompts": [
            ("explain <topic>", "Get an explanation of any topic"),
            ("fix <issue>", "Ask Claude to fix a bug or issue"),
            ("review <file>", "Get code review for a file"),
            ("test <code>", "Generate tests for your code"),
            ("refactor <code>", "Improve code structure"),
        ],
        "File Operations": [
            ("read <path>", "Read contents of a file"),
            ("write <path>", "Create or edit a file"),
            ("search <pattern>", "Search for files or code"),
            ("list <dir>", "List directory contents"),
        ],
        "Pro Tips": [
            ("Be specific", "More details = better results"),
            ("Use context", "Reference files or code"),
            ("Multi-step", "Break complex tasks into steps"),
            ("Follow up", "Ask clarifying questions"),
        ],
    }

    for section, items in sections.items():
        print(colorize(f"  {section}:", Colors.GREEN, Colors.BOLD))
        for shortcode, desc in items:
            print(
                f"    {colorize(shortcode, Colors.MAGENTA):25} {colorize(desc, Colors.DIM)}"
            )
        print()


def print_welcome() -> None:
    """Print the welcome message."""
    print_header()
    print(colorize("  Welcome! Type your questions or prompts below.", Colors.WHITE))
    print(colorize("  Type /help for commands or /info for shortcuts.", Colors.DIM))
    print()
    print(colorize("─" * 65, Colors.DIM))
    print()


def format_response(msg: AssistantMessage | UserMessage | ResultMessage) -> str:
    """Format a message for display."""
    parts = []

    if isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                parts.append(block.text)
            elif isinstance(block, ToolUseBlock):
                parts.append(
                    colorize(
                        f"[🔧 Using tool: {block.name}]", Colors.YELLOW, Colors.DIM
                    )
                )

    elif isinstance(msg, UserMessage):
        content = msg.content if isinstance(msg.content, list) else []
        for block in content:
            if isinstance(block, ToolResultBlock) and block.content:
                result = str(block.content)
                if len(result) > 150:
                    result = result[:150] + "..."
                parts.append(colorize(f"[📋 Tool result: {result}]", Colors.DIM))

    return "\n".join(parts)


async def run_interactive_session() -> None:
    """Run the interactive terminal session."""
    print_welcome()

    client: ClaudeSDKClient | None = None

    try:
        async with ClaudeSDKClient() as client:
            print(colorize("✓ Connected to Claude", Colors.GREEN))
            print()

            while True:
                try:
                    # Get user input
                    prompt = input(colorize("You: ", Colors.CYAN, Colors.BOLD))
                    prompt = prompt.strip()

                    if not prompt:
                        continue

                    # Handle special commands
                    if prompt.lower() in ("/quit", "/exit", "quit", "exit"):
                        print()
                        print(colorize("👋 Goodbye!", Colors.YELLOW))
                        break

                    if prompt.lower() in ("/help", "help"):
                        print_help()
                        continue

                    if prompt.lower() in ("/info", "info"):
                        print_info()
                        continue

                    if prompt.lower() in ("/clear", "clear"):
                        os.system("cls" if os.name == "nt" else "clear")
                        print_welcome()
                        print(colorize("✓ Connected to Claude", Colors.GREEN))
                        print()
                        continue

                    # Send query to Claude
                    print()
                    print(
                        colorize("Claude: ", Colors.GREEN, Colors.BOLD),
                        end="",
                        flush=True,
                    )

                    await client.query(prompt)

                    first_text = True
                    async for msg in client.receive_response():
                        response = format_response(msg)
                        if response:
                            if first_text:
                                print(response)
                                first_text = False
                            else:
                                print(response)

                        if isinstance(msg, ResultMessage):
                            if msg.total_cost_usd and msg.total_cost_usd > 0:
                                print()
                                print(
                                    colorize(
                                        f"[Cost: ${msg.total_cost_usd:.4f}]", Colors.DIM
                                    )
                                )
                            break

                    print()

                except KeyboardInterrupt:
                    print()
                    print(
                        colorize("\n[Interrupted - type /quit to exit]", Colors.YELLOW)
                    )
                    continue

    except Exception as e:
        print()
        print(colorize(f"Error: {e}", Colors.RED))
        print(
            colorize(
                "Make sure Claude Code CLI is installed and configured.", Colors.DIM
            )
        )
        print()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print()
        print(colorize("👋 Goodbye!", Colors.YELLOW))


if __name__ == "__main__":
    main()
