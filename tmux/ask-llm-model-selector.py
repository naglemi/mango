#!/usr/bin/env python3
"""
Ask LLM Model Selector - Multi-select checkbox interface for choosing LLM models
Supports selecting multiple models for comparison or single model for focused queries
"""

import os
import sys
import termios
import tty
from typing import List, Set, Dict, Tuple

class AskLLMModelSelector:
    """Interactive model selector with checkbox interface for LLM queries."""

    def __init__(self):
        # Available LLM models with their MCP tool names and descriptions
        self.models = [
            ("deepseek", "mcp__deepseek-proxy__deepseek_chat", "DeepSeek R1 - Strong reasoning and code"),
            ("gpt5", "mcp__gpt5-proxy__gpt5_chat", "GPT-5 - Latest OpenAI model"),
            ("grok", "mcp__grok-proxy__grok_chat", "Grok-4 - X.AI's conversational model"),
        ]

        self.selected_models: Set[str] = set()
        self.current_index = 0
        self.comparison_mode = False

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_menu(self):
        """Display the checkbox menu."""
        self._clear_screen()

        print(" Ask LLM - Model Selection")
        print("=" * 70)
        print("Select one or more language models to query:")
        print()
        print("Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit, c toggle comparison mode")
        print("=" * 70)
        print()

        # Display model list with checkboxes
        for i, (model_name, _, description) in enumerate(self.models):
            # Checkbox
            checkbox = "" if model_name in self.selected_models else ""

            # Highlight current selection
            if i == self.current_index:
                print(f"> {checkbox} {model_name.upper():<8} - {description}")
            else:
                print(f"  {checkbox} {model_name.upper():<8} - {description}")

        print()
        print(f"Selected: {len(self.selected_models)} models")

        if len(self.selected_models) > 1:
            mode_text = "COMPARISON MODE" if self.comparison_mode else "SEQUENTIAL MODE"
            print(f"Mode: {mode_text}")
            print("(Press 'c' to toggle between comparison and sequential modes)")

        print()
        if self.selected_models:
            print("Selected models:", ", ".join(sorted(self.selected_models)))

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

            # Handle arrow keys (escape sequences)
            if ch == '\033':
                ch += sys.stdin.read(1)  # [
                if ch == '\033[':
                    ch += sys.stdin.read(1)  # A, B, C, or D

            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_input(self, key: str) -> bool:
        """Handle keyboard input. Returns False to exit."""
        if key == 'q':
            return False

        elif key == '\033[A':  # Up arrow
            self.current_index = max(0, self.current_index - 1)

        elif key == '\033[B':  # Down arrow
            self.current_index = min(len(self.models) - 1, self.current_index + 1)

        elif key == ' ':  # Space - toggle selection
            if self.models:
                model_name, _, _ = self.models[self.current_index]
                if model_name in self.selected_models:
                    self.selected_models.remove(model_name)
                else:
                    self.selected_models.add(model_name)

        elif key == 'c':  # Toggle comparison mode
            if len(self.selected_models) > 1:
                self.comparison_mode = not self.comparison_mode

        elif key == '\r' or key == '\n':  # Enter - confirm selection
            if self.selected_models:
                return False
            else:
                # Must select at least one model
                pass

        return True

    def run_menu(self) -> Tuple[List[Tuple[str, str]], bool]:
        """
        Run the interactive menu and return selected models and mode.
        Returns: ([(model_name, mcp_tool_name), ...], comparison_mode)
        """
        # Check if running in an interactive terminal
        if not sys.stdin.isatty():
            print("Error: This tool requires an interactive terminal", file=sys.stderr)
            return [], False

        try:
            while True:
                self._display_menu()
                key = self._get_char()

                if not self._handle_input(key):
                    break

        except (KeyboardInterrupt, EOFError):
            print("\nCanceled.")
            return [], False

        # Clear screen and show final selection
        self._clear_screen()

        print(" Ask LLM - Model Selection Complete")
        print("=" * 70)

        selected_info = []
        for model_name, mcp_tool, description in self.models:
            if model_name in self.selected_models:
                selected_info.append((model_name, mcp_tool))
                print(f"   {model_name.upper():<8} - {description}")

        if len(selected_info) > 1:
            mode_text = "COMPARISON MODE" if self.comparison_mode else "SEQUENTIAL MODE"
            print(f"\nMode: {mode_text}")
            if self.comparison_mode:
                print("  → Responses will be displayed side-by-side for comparison")
            else:
                print("  → Models will be queried one after another")

        print()
        return selected_info, self.comparison_mode

def main():
    """Main entry point."""
    try:
        selector = AskLLMModelSelector()
        selected_models, comparison_mode = selector.run_menu()

        if selected_models:
            # Output selection for shell consumption
            model_names = [name for name, _ in selected_models]
            mcp_tools = [tool for _, tool in selected_models]

            print("SELECTED_MODELS=" + " ".join(model_names))
            print("MCP_TOOLS=" + " ".join(mcp_tools))
            print("COMPARISON_MODE=" + ("true" if comparison_mode else "false"))
        else:
            print("SELECTED_MODELS=")
            print("MCP_TOOLS=")
            print("COMPARISON_MODE=false")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()