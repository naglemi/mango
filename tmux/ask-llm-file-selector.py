#!/usr/bin/env python3
"""
Ask LLM File Selector - Enhanced checkbox interface for selecting any files to include in LLM queries
Based on file-grab-menu.py but expanded for broader file type support
"""

import os
import sys
import termios
import tty
from pathlib import Path
from typing import List, Set, Dict, Tuple

class AskLLMFileSelector:
    """Interactive file selector with checkbox interface for LLM queries."""

    def __init__(self, start_dir: str = "."):
        self.start_dir = Path(start_dir).resolve()
        self.selected_files: Set[str] = set()
        self.current_index = 0
        self.max_file_size = 1024 * 1024  # 1MB default limit
        self.all_files = self._discover_files()

    def _discover_files(self) -> List[Tuple[str, str, int]]:
        """Discover all relevant files up to 3 levels deep."""
        # Common file extensions for code, config, docs, data
        relevant_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.hpp',
            '.sh', '.bash', '.zsh', '.fish', '.pl', '.rb', '.php', '.lua', '.r', '.scala', '.kt',
            '.swift', '.m', '.mm', '.cs', '.vb', '.fs', '.clj', '.hs', '.elm', '.erl', '.ex', '.jl',
            '.md', '.rst', '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.xml', '.html', '.htm', '.css', '.scss', '.sass', '.less', '.sql', '.graphql',
            '.dockerfile', '.dockerignore', '.gitignore', '.env', '.envrc', 'makefile', '.mk',
            '.ipynb', '.py', '.rmd', '.qmd', '.tex', '.bib', '.csv', '.tsv', '.log'
        }

        files = []

        try:
            # Recursively scan up to 3 levels
            for root, dirs, filenames in os.walk(self.start_dir):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                    'node_modules', '__pycache__', '.git', '.venv', 'venv', 'env',
                    'build', 'dist', 'target', 'bin', 'obj', '.next', '.nuxt'
                }]

                # Limit depth to 3 levels
                level = len(Path(root).relative_to(self.start_dir).parts)
                if level > 3:
                    continue

                for filename in filenames:
                    file_path = Path(root) / filename

                    # Skip hidden files, very large files, and binary files
                    if filename.startswith('.'):
                        continue

                    try:
                        file_size = file_path.stat().st_size
                        if file_size > self.max_file_size:
                            continue

                        # Check if file has relevant extension or no extension but seems like text
                        file_ext = file_path.suffix.lower()
                        has_relevant_ext = (
                            file_ext in relevant_extensions or
                            filename.lower() in {'makefile', 'dockerfile', 'readme', 'license', 'changelog', 'todo'}
                        )

                        if has_relevant_ext:
                            relative_path = str(file_path.relative_to(self.start_dir))
                            files.append((relative_path, str(file_path), file_size))

                    except (OSError, ValueError):
                        continue

        except PermissionError:
            print(f"Error: Permission denied accessing {self.start_dir}")
            sys.exit(1)

        # Sort by relative path for consistent display
        files.sort(key=lambda x: x[0])
        return files

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes//1024}KB"
        else:
            return f"{size_bytes//(1024*1024)}MB"

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_menu(self):
        """Display the checkbox menu."""
        self._clear_screen()

        print(" Ask LLM - File Selection")
        print("=" * 60)
        print(f" Directory: {self.start_dir}")
        print(f" Found {len(self.all_files)} relevant files")
        print(f" Max file size: {self._format_file_size(self.max_file_size)}")
        print()
        print("Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit, s toggle size limit")
        print("=" * 60)
        print()

        if not self.all_files:
            print("No relevant files found in current directory tree.")
            print("Press any key to exit...")
            return

        # Display file list with checkboxes
        display_start = max(0, self.current_index - 15)
        display_end = min(len(self.all_files), display_start + 30)

        if display_start > 0:
            print("  ...")

        for i in range(display_start, display_end):
            relative_path, full_path, file_size = self.all_files[i]

            # Checkbox
            checkbox = "" if full_path in self.selected_files else ""

            # Format with size
            size_str = self._format_file_size(file_size)

            # Highlight current selection
            if i == self.current_index:
                print(f"> {checkbox} {relative_path} ({size_str})")
            else:
                print(f"  {checkbox} {relative_path} ({size_str})")

        if display_end < len(self.all_files):
            print("  ...")

        print()
        print(f"Selected: {len(self.selected_files)} files")

        # Show total size of selected files
        if self.selected_files:
            total_size = sum(
                file_size for _, full_path, file_size in self.all_files
                if full_path in self.selected_files
            )
            print(f"Total size: {self._format_file_size(total_size)}")

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
            self.current_index = min(len(self.all_files) - 1, self.current_index + 1)

        elif key == ' ':  # Space - toggle selection
            if self.all_files:
                _, full_path, _ = self.all_files[self.current_index]
                if full_path in self.selected_files:
                    self.selected_files.remove(full_path)
                else:
                    self.selected_files.add(full_path)

        elif key == 's':  # Toggle size limit
            if self.max_file_size == 1024 * 1024:  # 1MB
                self.max_file_size = 10 * 1024 * 1024  # 10MB
            else:
                self.max_file_size = 1024 * 1024  # 1MB

            # Rediscover files with new size limit
            self.all_files = self._discover_files()
            self.current_index = 0
            # Remove any selected files that no longer qualify
            valid_paths = {full_path for _, full_path, _ in self.all_files}
            self.selected_files = self.selected_files.intersection(valid_paths)

        elif key == '\r' or key == '\n':  # Enter - confirm selection
            return False

        return True

    def run_menu(self) -> List[str]:
        """Run the interactive menu and return selected files."""
        # Check if running in an interactive terminal
        if not sys.stdin.isatty():
            print("Error: This tool requires an interactive terminal", file=sys.stderr)
            return []

        if not self.all_files:
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

        print(" Ask LLM - File Selection Complete")
        print("=" * 60)
        print(f"Selected {len(selected_files)} files:")

        total_size = 0
        for file_path in sorted(selected_files):
            relative = str(Path(file_path).relative_to(self.start_dir))
            # Find file size
            file_size = next((size for _, fp, size in self.all_files if fp == file_path), 0)
            total_size += file_size
            print(f"   {relative} ({self._format_file_size(file_size)})")

        if selected_files:
            print(f"\nTotal: {self._format_file_size(total_size)}")
        print()

        return selected_files

def main():
    """Main entry point."""
    start_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    try:
        selector = AskLLMFileSelector(start_dir)
        selected_files = selector.run_menu()

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