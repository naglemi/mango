#!/usr/bin/env python3
"""
Interactive menu for creating hooks with user-friendly interface.
"""

import json
import os
import sys
import termios
import tty
import subprocess
import tempfile
from typing import Optional, Dict, Any

class HookCreator:
    def __init__(self):
        self.mango_path = os.path.expanduser("~/mango")
        self.hooks_dir = os.path.join(self.mango_path, "hooks")

    def _getch(self) -> str:
        """Get a single character from stdin without pressing Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def _clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="", flush=True)

    def _get_user_input(self, prompt: str) -> str:
        """Get multi-line user input."""
        print(f"\n{prompt}")
        print("(Press Enter twice when done, or Ctrl+C to cancel)")
        print("-" * 50)

        lines = []
        empty_lines = 0

        try:
            while True:
                line = input()
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        break
                    lines.append(line)
                else:
                    empty_lines = 0
                    lines.append(line)
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

        return "\n".join(lines).strip()

    def _get_scope_choice(self) -> str:
        """Get scope choice from user (local or global)."""
        while True:
            self._clear_screen()
            print(" Hook Scope Selection")
            print("=" * 40)
            print()
            print("Where should this hook be applied?")
            print()
            print("  [L] Local Project Only")
            print("      - Applied only to current project")
            print("      - Stored in project's hook config")
            print()
            print("  [G] Global (All Projects)")
            print("      - Applied to all projects using these hooks")
            print("      - Added to mango repo and committed")
            print("      - Hooks installation will be rerun automatically")
            print()
            print("  [C] Cancel")
            print()
            print("Choice [L/G/C]: ", end="", flush=True)

            choice = self._getch().upper()
            if choice in ['L', 'G', 'C']:
                print(choice)
                return choice
            else:
                print(f"\nInvalid choice: {choice}. Please press L, G, or C.")
                input("Press Enter to continue...")

    def _create_hook_file(self, command: str, message: str) -> str:
        """Create a hook file and return its path."""
        # Generate a reasonable filename based on the command
        safe_name = "".join(c for c in command if c.isalnum() or c in '-_').lower()
        if not safe_name:
            safe_name = "custom_block"

        filename = f"block-{safe_name}.py"
        filepath = os.path.join(self.hooks_dir, filename)

        # Make sure filename is unique
        counter = 1
        while os.path.exists(filepath):
            filename = f"block-{safe_name}-{counter}.py"
            filepath = os.path.join(self.hooks_dir, filename)
            counter += 1

        # Create the hook file content
        hook_content = f'''#!/usr/bin/env python3
"""
Block {command} command with custom message.
Auto-generated hook.
"""

import sys
import json
import re

def main():
    # Read the command from stdin
    try:
        data = json.loads(sys.stdin.read())
        command = data.get('command', '')
    except:
        # Fallback: read command as plain text
        command = sys.stdin.read().strip()

    # Check if command contains the blocked pattern
    if re.search(r'\\b{re.escape(command)}\\b', command, re.IGNORECASE):
        print("{message}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
'''

        # Write the hook file
        with open(filepath, 'w') as f:
            f.write(hook_content)

        # Make it executable
        os.chmod(filepath, 0o755)

        return filepath

    def _add_to_hook_registry(self, hook_filename: str, command: str, message: str):
        """Add the hook to the hook registry."""
        registry_path = os.path.join(self.hooks_dir, "hook_registry.json")

        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            registry = {}

        # Add the hook
        hook_id = os.path.splitext(hook_filename)[0]  # Remove .py extension
        registry[hook_id] = {
            "name": f"Block {command}",
            "description": f"Blocks the '{command}' command",
            "filename": hook_filename,
            "enabled": True,
            "custom": True
        }

        # Write back to registry
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

    def _commit_global_changes(self, hook_filename: str, command: str):
        """Commit the hook to git and rerun hooks installation."""
        try:
            # Change to mango directory
            os.chdir(self.mango_path)

            print("\n Committing hook to git...")

            # Add the files
            subprocess.run(['git', 'add', f'hooks/{hook_filename}'], check=True)
            subprocess.run(['git', 'add', 'hooks/hook_registry.json'], check=True)

            # Commit
            commit_msg = f"Add custom hook to block '{command}' command"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

            print(" Changes committed to git")

            # Rerun hooks installation
            print("\n Reinstalling hooks...")
            install_script = os.path.join(self.hooks_dir, "install.sh")
            if os.path.exists(install_script):
                subprocess.run(['bash', install_script], check=True)
                print(" Hooks installation complete")
            else:
                print("  Warning: install.sh not found, manual installation may be required")

        except subprocess.CalledProcessError as e:
            print(f" Error during git operations: {e}")
            return False
        except Exception as e:
            print(f" Unexpected error: {e}")
            return False

        return True

    def run(self):
        """Run the interactive hook creation process."""
        try:
            self._clear_screen()
            print(" Create Hook")
            print("=" * 40)
            print()
            print("This wizard will help you create a hook to block specific commands.")
            print()

            # Get command to block
            command = self._get_user_input(" What command should be blocked? (e.g., 'rm -rf', 'git push --force', etc.)")
            if not command.strip():
                print(" No command specified. Exiting.")
                return

            # Get message to display
            message = self._get_user_input(" What message should be displayed when this command is blocked?")
            if not message.strip():
                message = f"Command '{command}' is blocked for safety reasons."

            # Get scope choice
            scope = self._get_scope_choice()
            if scope == 'C':
                print("Cancelled.")
                return

            # Create the hook file
            print(f"\n Creating hook file...")
            hook_filename = os.path.basename(self._create_hook_file(command, message))
            print(f" Created {hook_filename}")

            # Add to registry
            print(" Adding to hook registry...")
            self._add_to_hook_registry(hook_filename, command, message)
            print(" Added to registry")

            if scope == 'G':
                # Global scope - commit and reinstall
                if self._commit_global_changes(hook_filename, command):
                    print(f"\n Global hook successfully created!")
                    print(f"   Command blocked: {command}")
                    print(f"   Message: {message}")
                    print("   Applied globally to all projects")
                else:
                    print(f"\n  Hook created but git operations failed.")
                    print("   You may need to manually commit and reinstall hooks.")
            else:
                # Local scope
                print(f"\n Local hook successfully created!")
                print(f"   Command blocked: {command}")
                print(f"   Message: {message}")
                print("   Applied to current project only")

            print(f"\nHook file: {os.path.join(self.hooks_dir, hook_filename)}")

        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
        except Exception as e:
            print(f"\n Error creating hook: {e}")

if __name__ == "__main__":
    creator = HookCreator()
    creator.run()