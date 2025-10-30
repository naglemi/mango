#!/usr/bin/env python3
"""
Ask LLM Context Selector - Interface for selecting previous responses to include as context
"""

import os
import sys
import termios
import tty
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
from ask_llm_output_manager import AskLLMOutputManager

class AskLLMContextSelector:
    """Interactive selector for previous LLM responses to use as context."""

    def __init__(self, base_dir: str = "/home/ubuntu/mango/ask_llm_outputs"):
        self.output_manager = AskLLMOutputManager(base_dir)
        self.available_contexts: List[Tuple[str, str, Path]] = []  # (model, timestamp, file_path)
        self.selected_contexts: Set[int] = set()  # indices into available_contexts
        self.current_index = 0
        self._load_available_contexts()

    def _load_available_contexts(self):
        """Load all available previous responses across all models."""
        base_path = Path(self.output_manager.base_dir)

        for model_dir in base_path.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                if model_name == "comparison":  # Skip comparison files for now
                    continue

                # Get previous responses for this model
                responses = self.output_manager.list_previous_responses(model_name, limit=20)
                for timestamp, file_path in responses:
                    self.available_contexts.append((model_name, timestamp, file_path))

        # Sort by timestamp (newest first)
        self.available_contexts.sort(key=lambda x: x[1], reverse=True)

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_menu(self):
        """Display the context selection menu."""
        self._clear_screen()

        print(" Ask LLM - Previous Response Context")
        print("=" * 70)
        print("Select previous responses to include as context:")
        print()
        print("Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit, p preview")
        print("=" * 70)
        print()

        if not self.available_contexts:
            print("No previous responses found.")
            print("Press any key to continue without context...")
            return

        # Display available contexts with checkboxes
        display_start = max(0, self.current_index - 10)
        display_end = min(len(self.available_contexts), display_start + 20)

        if display_start > 0:
            print("  ...")

        for i in range(display_start, display_end):
            model_name, timestamp, file_path = self.available_contexts[i]

            # Checkbox
            checkbox = "" if i in self.selected_contexts else ""

            # Highlight current selection
            if i == self.current_index:
                print(f"> {checkbox} {model_name.upper():<8} - {timestamp}")
            else:
                print(f"  {checkbox} {model_name.upper():<8} - {timestamp}")

        if display_end < len(self.available_contexts):
            print("  ...")

        print()
        print(f"Selected: {len(self.selected_contexts)} contexts")

        if self.available_contexts:
            print(f"Total available: {len(self.available_contexts)} previous responses")

    def _show_preview(self, index: int):
        """Show preview of selected context."""
        if 0 <= index < len(self.available_contexts):
            model_name, timestamp, file_path = self.available_contexts[index]

            self._clear_screen()
            print(" PREVIEW")
            print("=" * 70)
            print(f"Model: {model_name.upper()}")
            print(f"Time: {timestamp}")
            print("=" * 70)

            # Show first 30 lines of the context
            context = self.output_manager.extract_context_from_response(file_path, include_files=False)
            lines = context.split('\n')

            for i, line in enumerate(lines[:30]):
                print(line)
                if i == 29 and len(lines) > 30:
                    print(f"\n... ({len(lines) - 30} more lines)")

            print("\n" + "=" * 70)
            print("Press any key to return to selection...")

            # Wait for any key
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

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
            if self.available_contexts:
                self.current_index = min(len(self.available_contexts) - 1, self.current_index + 1)

        elif key == ' ':  # Space - toggle selection
            if self.available_contexts:
                if self.current_index in self.selected_contexts:
                    self.selected_contexts.remove(self.current_index)
                else:
                    self.selected_contexts.add(self.current_index)

        elif key == 'p':  # Preview
            if self.available_contexts and 0 <= self.current_index < len(self.available_contexts):
                self._show_preview(self.current_index)

        elif key == '\r' or key == '\n':  # Enter - confirm selection
            return False

        return True

    def run_menu(self) -> List[str]:
        """
        Run the interactive menu and return selected context strings.
        Returns: List of context strings to include in the prompt
        """
        # Check if running in an interactive terminal
        if not sys.stdin.isatty():
            print("Error: This tool requires an interactive terminal", file=sys.stderr)
            return []

        if not self.available_contexts:
            self._display_menu()
            input()  # Wait for keypress
            return []

        try:
            while True:
                self._display_menu()
                key = self._get_char()

                if not self._handle_input(key):
                    break

        except (KeyboardInterrupt, EOFError):
            print("\nCanceled.")
            return []

        # Extract selected contexts
        selected_contexts = []
        if self.selected_contexts:
            self._clear_screen()
            print(" Ask LLM - Context Selection Complete")
            print("=" * 70)
            print(f"Selected {len(self.selected_contexts)} contexts:")

            for i in sorted(self.selected_contexts):
                model_name, timestamp, file_path = self.available_contexts[i]
                print(f"   {model_name.upper():<8} - {timestamp}")

                # Extract context from this file
                context = self.output_manager.extract_context_from_response(
                    file_path, include_files=False
                )

                # Format context with header
                formatted_context = f"\n--- Context from {model_name.upper()} ({timestamp}) ---\n{context}\n"
                selected_contexts.append(formatted_context)

            print()
        else:
            # No contexts selected
            self._clear_screen()
            print(" No previous context selected - proceeding with fresh conversation.")

        return selected_contexts

def main():
    """Main entry point."""
    try:
        selector = AskLLMContextSelector()
        selected_contexts = selector.run_menu()

        if selected_contexts:
            print(f"CONTEXT_COUNT={len(selected_contexts)}")
            # Output contexts (could be large, so just indicate success)
            for i, context in enumerate(selected_contexts):
                print(f"CONTEXT_{i}={len(context)} characters")
        else:
            print("CONTEXT_COUNT=0")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()