#!/usr/bin/env python3
"""
Enhanced hooks menu that includes the option to create hooks.
This wraps the original hook_selector.py and adds the 'N' option.
"""

import os
import sys
import subprocess
import tempfile
import termios
import tty
from pathlib import Path

def get_key():
    """Get a single key press."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)

        # Handle special keys
        if key == '\x1b':  # ESC sequence
            key += sys.stdin.read(2)
            if key == '\x1b[A':
                return 'UP'
            elif key == '\x1b[B':
                return 'DOWN'
            elif key == '\x1b[C':
                return 'RIGHT'
            elif key == '\x1b[D':
                return 'LEFT'

        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="", flush=True)

def show_main_menu():
    """Show the main hooks menu with create option."""
    while True:
        clear_screen()
        print(" Hook Management")
        print("=" * 40)
        print()
        print("  [M] Manage Hooks - Enable/disable existing hooks")
        print("  [N] New Hook - Create a new blocking hook")
        print("  [Q] Quit")
        print()
        print("Choice [M/N/Q]: ", end="", flush=True)

        key = get_key().upper()

        if key == 'M':
            # Run the original hook selector
            hooks_dir = Path.home() / "mango" / "hooks"
            hook_selector = hooks_dir / "hook_selector.py"
            if hook_selector.exists():
                subprocess.run([sys.executable, str(hook_selector)])
            else:
                print(f"\nError: {hook_selector} not found")
                input("Press Enter to continue...")

        elif key == 'N':
            # Run the hook creator
            script_dir = Path(__file__).parent
            hook_creator = script_dir / "hook-creator.py"
            if hook_creator.exists():
                subprocess.run([sys.executable, str(hook_creator)])
            else:
                print(f"\nError: {hook_creator} not found")
                input("Press Enter to continue...")

        elif key in ['Q', '\x03']:  # Q or Ctrl+C
            break
        else:
            print(f"\nInvalid choice: {key}")
            input("Press Enter to continue...")

def main():
    """Main entry point."""
    # Check if running in terminal
    if not sys.stdout.isatty():
        print("Error: This tool requires an interactive terminal")
        sys.exit(1)

    try:
        show_main_menu()
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()