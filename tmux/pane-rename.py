#!/usr/bin/env python3
"""
Pane Rename Tool - Interactive interface for renaming tmux panes
"""

import os
import sys
import subprocess
from pathlib import Path

class PaneRename:
    """Simple tmux pane rename tool."""

    def __init__(self):
        # Check if we're in tmux
        if not os.environ.get('TMUX'):
            print(" This tool requires running inside a tmux session.")
            input("Press Enter to close...")
            sys.exit(1)

    def get_current_pane_title(self) -> str:
        """Get current pane title."""
        try:
            result = subprocess.run(
                ['tmux', 'display-message', '-p', '#{pane_title}'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def rename_pane(self, new_title: str):
        """Rename the current pane."""
        try:
            subprocess.run(
                ['tmux', 'select-pane', '-T', new_title],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f" Failed to rename pane: {e}")
            return False

    def run(self):
        """Run the pane rename tool."""
        print(" Rename Tmux Pane")
        print("=" * 30)
        print()

        # Show current title
        current_title = self.get_current_pane_title()
        if current_title:
            print(f"Current title: {current_title}")
        else:
            print("Current title: (no title set)")

        print()

        # Get new title from user
        try:
            new_title = input("Enter new pane title (or press Enter to cancel): ").strip()

            if not new_title:
                print("Cancelled.")
                return

            # Rename the pane
            if self.rename_pane(new_title):
                print(f" Pane renamed to: {new_title}")

        except KeyboardInterrupt:
            print("\nCancelled.")
        except EOFError:
            print("\nCancelled.")

def main():
    """Main entry point."""
    try:
        renamer = PaneRename()
        renamer.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()