#!/usr/bin/env python3
"""
Buffer Copy Menu - Interactive interface for copying tmux buffer content
Allows user to choose destination (file/clipboard) and scope (all/recent X lines)
"""

import os
import sys
import termios
import tty
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

class BufferCopyMenu:
    """Interactive menu for copying tmux buffer content."""

    def __init__(self):
        self.destination = "clipboard"  # clipboard or file
        self.scope = "all"  # all or recent
        self.line_count = 100  # for recent option
        self.current_selection = 0
        self.menu_items = [
            {"id": "destination", "name": "Destination", "options": ["Clipboard", "File"]},
            {"id": "scope", "name": "Content Scope", "options": ["All Lines", "Recent Lines"]},
            {"id": "line_count", "name": "Line Count", "type": "number"},
            {"id": "execute", "name": " Copy Buffer", "type": "action"}
        ]

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _get_buffer_content(self) -> Optional[str]:
        """Get tmux buffer content."""
        try:
            if self.scope == "all":
                # Capture entire scrollback buffer from previous pane
                result = subprocess.run(
                    ['tmux', 'capture-pane', '-t', '-1', '-S', '-', '-p'],
                    capture_output=True, text=True, check=True
                )
            else:
                # Capture recent lines from previous pane
                result = subprocess.run(
                    ['tmux', 'capture-pane', '-t', '-1', '-S', f'-{self.line_count}', '-p'],
                    capture_output=True, text=True, check=True
                )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error capturing tmux buffer: {e}")
            return None
        except FileNotFoundError:
            print("Error: tmux command not found. Are you running this from within tmux?")
            return None

    def _save_to_clipboard(self, content: str) -> bool:
        """Save content to system clipboard."""
        try:
            # First try tmux's own clipboard buffer
            try:
                subprocess.run(
                    ['tmux', 'set-buffer', content],
                    check=True, capture_output=True
                )
                print(" Content saved to tmux clipboard buffer")
                print("   Use 'tmux show-buffer' to view or 'Ctrl+b ]' to paste")

                # For SSH sessions, also display content for manual copying
                if os.environ.get('SSH_CONNECTION'):
                    print("\n" + "="*50)
                    print(" Content (select and copy manually):")
                    print("="*50)
                    print(content)
                    print("="*50)

                return True
            except subprocess.CalledProcessError:
                pass

            # Try system clipboard commands
            clipboard_commands = [
                ['xclip', '-selection', 'clipboard'],
                ['xsel', '--clipboard', '--input'],
                ['pbcopy'],  # macOS
            ]

            for cmd in clipboard_commands:
                try:
                    subprocess.run(
                        cmd, input=content, text=True, check=True,
                        capture_output=True
                    )
                    print(" Content copied to system clipboard")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            # If we're over SSH, suggest file save instead
            if os.environ.get('SSH_CONNECTION'):
                print("  SSH session detected - system clipboard not available")
                print(" Recommend saving to file instead for easy access")
            else:
                print("  No clipboard utility found (xclip, xsel, pbcopy)")

            return False

        except Exception as e:
            print(f" Error copying to clipboard: {e}")
            return False

    def _save_to_file(self, content: str) -> bool:
        """Save content to a file."""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tmux_buffer_{timestamp}.txt"

            # Ask user for filename (with default)
            print(f"\nDefault filename: {filename}")
            user_filename = input("Enter filename (or press Enter for default): ").strip()

            if user_filename:
                filename = user_filename

            # Save to current directory
            filepath = Path(filename).resolve()

            with open(filepath, 'w') as f:
                f.write(content)

            print(f"Buffer saved to: {filepath}")
            return True

        except Exception as e:
            print(f"Error saving to file: {e}")
            return False

    def _display_menu(self):
        """Display the buffer copy menu."""
        self._clear_screen()

        print(" Buffer Copy Menu")
        print("=" * 50)
        print("Controls: ↑↓/WS navigate, ←→/AD change values, ENTER execute, q quit")
        print("=" * 50)
        print()

        for i, item in enumerate(self.menu_items):
            prefix = "> " if i == self.current_selection else "  "

            if item["id"] == "destination":
                value = " File" if self.destination == "file" else " Clipboard"
                print(f"{prefix}{item['name']}: {value}")

            elif item["id"] == "scope":
                if self.scope == "all":
                    value = " All Lines"
                else:
                    value = f" Recent {self.line_count} Lines"
                print(f"{prefix}{item['name']}: {value}")

            elif item["id"] == "line_count":
                status = "(active)" if self.scope == "recent" else "(inactive)"
                print(f"{prefix}{item['name']}: {self.line_count} {status}")

            elif item["id"] == "execute":
                print(f"{prefix}{item['name']}")

            print()

        print("=" * 50)
        print("Current Settings:")
        print(f"  Destination: {'File' if self.destination == 'file' else 'Clipboard'}")
        scope_desc = "All buffer content" if self.scope == "all" else f"Most recent {self.line_count} lines"
        print(f"  Content: {scope_desc}")

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

        elif key == '\033[A' or key == 'w' or key == 'W':  # Up arrow or W
            self.current_selection = max(0, self.current_selection - 1)

        elif key == '\033[B' or key == 's' or key == 'S':  # Down arrow or S
            self.current_selection = min(len(self.menu_items) - 1, self.current_selection + 1)

        elif key == '\033[C' or key == '\033[D' or key == 'a' or key == 'A' or key == 'd' or key == 'D':  # Left/Right arrows or A/D - change values
            current_item = self.menu_items[self.current_selection]

            if current_item["id"] == "destination":
                self.destination = "file" if self.destination == "clipboard" else "clipboard"

            elif current_item["id"] == "scope":
                self.scope = "recent" if self.scope == "all" else "all"

            elif current_item["id"] == "line_count" and self.scope == "recent":
                if key == '\033[C' or key == 'd' or key == 'D':  # Right arrow or D - increase
                    self.line_count = min(10000, self.line_count + 50)
                elif key == '\033[D' or key == 'a' or key == 'A':  # Left arrow or A - decrease
                    self.line_count = max(10, self.line_count - 50)

        elif key == '\r' or key == '\n':  # Enter - execute with current settings
            return self._execute_copy()

        return True

    def _execute_copy(self) -> bool:
        """Execute the buffer copy operation."""
        print("\n Copying buffer content...")

        # Get buffer content
        content = self._get_buffer_content()
        if not content:
            print(" Failed to get buffer content")
            return False

        # Show content preview
        lines = content.split('\n')
        print(f" Buffer contains {len(lines)} lines")

        if self.scope == "recent" and len(lines) > self.line_count:
            print(f" Will copy most recent {self.line_count} lines")
            # Take the last N lines
            content = '\n'.join(lines[-self.line_count:])

        # Execute copy operation
        if self.destination == "clipboard":
            success = self._save_to_clipboard(content)
            if success:
                print(" Content copied to clipboard!")
            else:
                print(" Failed to copy to clipboard")
        else:
            success = self._save_to_file(content)
            if success:
                print(" Content saved to file!")
            else:
                print(" Failed to save to file")

        return False

    def run_menu(self):
        """Run the interactive buffer copy menu."""
        try:
            while True:
                self._display_menu()
                key = self._get_char()

                if not self._handle_input(key):
                    break

        except KeyboardInterrupt:
            print("\n Buffer copy canceled.")
            return

        print("\n Buffer copy menu closed.")

def main():
    """Main entry point."""
    # Check if we're in tmux
    if not os.environ.get('TMUX'):
        print(" This tool requires running inside a tmux session.")
        print("Start tmux first, then run this command.")
        sys.exit(1)

    try:
        menu = BufferCopyMenu()
        menu.run_menu()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()