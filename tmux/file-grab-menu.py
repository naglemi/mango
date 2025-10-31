#!/usr/bin/env python3
"""
File Grab Menu - Checkbox interface for selecting scripts to concatenate
Based on hook_selector.py interface patterns
"""

import os
import sys
import termios
import tty
from pathlib import Path
from typing import List, Set, Dict, Tuple

class FileGrabMenu:
    """Interactive file selector with checkbox interface."""

    def __init__(self, start_dir: str = "."):
        self.start_dir = Path(start_dir).resolve()
        self.script_files = self._discover_scripts()
        self.selected_files: Set[str] = set()
        self.current_index = 0

    def _discover_scripts(self) -> List[Tuple[str, str]]:
        """Discover script files up to 2 levels deep."""
        script_extensions = {'.sh', '.py', '.js', '.pl', '.rb', '.php', '.go', '.rs'}
        scripts = []

        try:
            # Level 0: current directory
            for item in self.start_dir.iterdir():
                if item.is_file() and item.suffix in script_extensions:
                    relative_path = str(item.relative_to(self.start_dir))
                    scripts.append((relative_path, str(item)))

            # Level 1: subdirectories
            for subdir in self.start_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    try:
                        for item in subdir.iterdir():
                            if item.is_file() and item.suffix in script_extensions:
                                relative_path = str(item.relative_to(self.start_dir))
                                scripts.append((relative_path, str(item)))
                    except PermissionError:
                        continue

            # Level 2: sub-subdirectories
            for subdir in self.start_dir.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    try:
                        for subsubdir in subdir.iterdir():
                            if subsubdir.is_dir() and not subsubdir.name.startswith('.'):
                                try:
                                    for item in subsubdir.iterdir():
                                        if item.is_file() and item.suffix in script_extensions:
                                            relative_path = str(item.relative_to(self.start_dir))
                                            scripts.append((relative_path, str(item)))
                                except PermissionError:
                                    continue
                    except PermissionError:
                        continue

        except PermissionError:
            print(f"Error: Permission denied accessing {self.start_dir}")
            sys.exit(1)

        # Sort by relative path for consistent display
        scripts.sort(key=lambda x: x[0])
        return scripts

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_menu(self):
        """Display the checkbox menu."""
        self._clear_screen()

        print(" File Grab Menu")
        print("=" * 50)
        print(f" Directory: {self.start_dir}")
        print(f" Found {len(self.script_files)} script files")
        print()
        print("Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit")
        print("=" * 50)
        print()

        if not self.script_files:
            print("No script files found in current directory tree.")
            print("Press any key to exit...")
            return

        # Display file list with checkboxes
        display_start = max(0, self.current_index - 10)
        display_end = min(len(self.script_files), display_start + 20)

        if display_start > 0:
            print("  ...")

        for i in range(display_start, display_end):
            relative_path, full_path = self.script_files[i]

            # Checkbox
            checkbox = "" if full_path in self.selected_files else ""

            # Highlight current selection
            if i == self.current_index:
                print(f"> {checkbox} {relative_path}")
            else:
                print(f"  {checkbox} {relative_path}")

        if display_end < len(self.script_files):
            print("  ...")

        print()
        print(f"Selected: {len(self.selected_files)} files")

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
            self.current_index = min(len(self.script_files) - 1, self.current_index + 1)

        elif key == ' ':  # Space - toggle selection
            if self.script_files:
                _, full_path = self.script_files[self.current_index]
                if full_path in self.selected_files:
                    self.selected_files.remove(full_path)
                else:
                    self.selected_files.add(full_path)

        elif key == '\r' or key == '\n':  # Enter - confirm selection
            return False

        return True

    def run_menu(self) -> List[str]:
        """Run the interactive menu and return selected files."""

        if not self.script_files:
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

        # Clear screen and show final selection
        self._clear_screen()
        selected_files = [f for f in self.selected_files]

        print(" File Grab Menu - Selection Complete")
        print("=" * 50)
        print(f"Selected {len(selected_files)} files:")
        for file_path in sorted(selected_files):
            relative = str(Path(file_path).relative_to(self.start_dir))
            print(f"   {relative}")
        print()

        return selected_files

def main():
    """Main entry point."""
    start_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    try:
        menu = FileGrabMenu(start_dir)
        selected_files = menu.run_menu()

        if selected_files:
            # Output selected files as space-separated list for shell consumption
            print("SELECTED_FILES=" + " ".join(f'"{f}"' for f in selected_files))
        else:
            print("SELECTED_FILES=")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()