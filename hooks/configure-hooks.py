#!/usr/bin/env python3
"""
Interactive hook configurator for Claude Code hooks
Allows users to select which hooks to install
"""

import os
import sys
import json
import termios
import tty
import socket
from pathlib import Path

# Hook definitions with detailed descriptions
# Format: (hook_id, name, description, category, default_enabled)
HOOKS = [
    # Security Hooks
    ("block-rm", "Block RM Commands", "Prevents dangerous 'rm' commands that could delete files. Use file manager or specific operations instead.", "security", True),
    ("block-git-stash", "Block Git Stash", "Prevents git stash commands which can hide work. Encourages explicit commits instead.", "security", True),
    ("block-dangerous-git", "Block Git Add -A", "Prevents 'git add -A' and 'git add .' commands. Use explicit file adds instead.", "security", False),
    ("protect-env-vars", "Protect Environment Variables", "Prevents modifications to critical environment variables like PATH, AWS credentials.", "security", True),
    ("block-python-inline", "Block Python -c", "Prevents inline Python execution (python -c). Create proper scripts in debugging_scripts/ instead.", "security", True),
    ("block-scripts-dirty-git", "Block Scripts with Dirty Git", "Prevents running scripts when git working tree is dirty. Encourages committing before execution.", "security", False),
    ("block-error-hiding", "Block Error Hiding", "Prevents bash commands with error hiding (2>/dev/null, || true). Errors should be visible.", "security", True),
    ("block-head-tail", "Block Head/Tail", "Prevents head/tail commands. Use Read tool instead for better control.", "security", False),
    ("block-search-tools", "Block Search Tools", "Prevents find/grep commands. Use Glob/Grep tools instead.", "security", False),
    ("block-hook-editing", "Block Hook Editing", "Prevents AI from editing hook files. Hooks should be managed by humans.", "security", True),
    ("block-sed-editing", "Block Sed Editing", "Prevents sed for editing. Use Edit tool instead for reviewable changes.", "security", True),
    ("block-all-scripts", "Block New Scripts", "Prevents creating any new script files. Extreme measure for production safety.", "security", False),
    ("block-scripts-outside-debug", "Scripts in Debug Dir Only", "Requires all new scripts to be in debugging_scripts/ directory. Keeps repo organized.", "security", False),
    ("block-glob-tool", "Block Glob Tool", "Prevents Glob tool usage. Forces reading specific files instead of pattern matching.", "security", False),
    ("block-grep-tool", "Block Grep Tool", "Prevents Grep tool usage. Forces reading entire files instead of searching.", "security", False),
    ("block-search-tool", "Block Search Tool", "Prevents Search tool usage. Part of enforcing full file reads.", "security", False),
    ("block-commit-to-main", "Block Main Branch Commits", "Prevents direct commits to main/master branch. Use feature branches.", "security", False),
    ("block-cd", "Block CD Commands", "Prevents 'cd' commands. Use absolute paths instead for clarity.", "security", False),
    ("block-homedir-edits", "Block Home Directory Edits", "Prevents editing files outside current project directory. Protects system files.", "security", True),

    # Code Quality Hooks
    ("block-error-handling", "Block Try/Catch", "Prevents excessive try/catch blocks. Encourages fail-fast, linear code.", "quality", False),
    ("python-lint-before-run", "Python Lint Before Run", "Auto-lints Python files before execution. Catches syntax errors early.", "quality", True),
    ("block-bad-filenames", "Block Bad Filenames", "Prevents files with spaces, special chars, or overly long names.", "quality", True),
    ("block-filename-proliferation", "Block Filename Proliferation", "Prevents _final, _v2, _fixed suffixes. Use version control instead.", "quality", True),
    ("limit-scripts-per-dir", "Limit Scripts Per Directory", "Limits number of script files per directory. Keeps repos organized.", "quality", False),
    ("limit-line-count", "Limit Line Count (Soft)", "Warns about files exceeding line limit (default: 300). Configurable.", "quality", False),
    ("strict-limit-line-count", "Strict Line Limit", "Blocks files exceeding line limit. Stricter version of limit-line-count.", "quality", False),
    ("block-md-files", "Block Markdown Files", "Prevents creating documentation files. For production-only projects.", "quality", False),
    ("block-reports-no-images", "Require Report Images", "Requires MCP reports to include images. Ensures visual documentation.", "quality", False),
    ("enforce-sequential-scripts", "Enforce Sequential Script Numbering", "Requires scripts to be numbered (01_, 02_, etc). Maintains execution order clarity.", "quality", False),
    ("block-file-versions", "Block File Versions", "Prevents creating versioned file copies (_v1, _v2). Use git instead.", "quality", True),
    ("block-dir-and-mv", "Block Dir and MV", "Prevents 'dir' and 'mv' commands. Use ls and specific file operations.", "quality", False),
    ("auto-lint-python", "Auto-Lint Python", "Automatically formats Python code before saving. Uses black/autopep8.", "quality", False),

    # Productivity Hooks
    ("notify-on-completion", "Completion Notifications", "Sends push notification when Claude finishes a task. Requires Pushover.", "productivity", False),

    # Execution Control
    ("force-foreground-bash", "Force Foreground Bash", "Forces all bash commands to run in foreground. Prevents background processes.", "control", False),
    ("force-background-bash", "Force Background Bash", "Forces all bash commands to run in background. Allows concurrent operations.", "control", False),
]

CATEGORIES = {
    "security": "Security & Safety",
    "quality": "Code Quality & Organization",
    "productivity": "Productivity & Notifications",
    "control": "Execution Control"
}

class HookConfigurator:
    """Interactive hook configurator using custom TUI."""

    def __init__(self, developer_mode=False):
        self.developer_mode = developer_mode

        # Group hooks by category
        self.sections = {
            "security": [],
            "quality": [],
            "productivity": [],
            "control": []
        }

        # Initialize enabled state with defaults
        self.enabled = {}

        # Check hostname for development environment
        # Try HOSTNAME env var first, then socket.gethostname()
        hostname = os.environ.get('HOSTNAME', '')
        if not hostname:
            try:
                hostname = socket.gethostname()
            except:
                hostname = ''
        hostname = hostname.lower()
        is_dev_host = 'exp' in hostname or '117' in hostname

        for i, (hook_id, name, description, category, default) in enumerate(HOOKS):
            self.sections[category].append(i)
            # In developer mode, enable all by default
            if developer_mode:
                self.enabled[i] = True
            # Enable notify-on-completion by default on development hosts
            elif hook_id == "notify-on-completion" and is_dev_host:
                self.enabled[i] = True
            else:
                self.enabled[i] = default

        self.selected_index = 0
        self.message = ""

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def _display_menu(self):
        """Display the menu with checkboxes."""
        self._clear_screen()

        # Header
        print("CLAUDE CODE HOOKS CONFIGURATOR")
        print("=" * 80)
        print("Use ↑/↓ or W/S to navigate | Space to toggle | A to select all | Enter to confirm | Q to cancel")
        print()

        current_item = 0

        # Display sections
        for section_name in ["security", "quality", "productivity", "control"]:
            section_title = CATEGORIES[section_name].upper()

            print(f"=== {section_title} ===")
            print()

            for hook_idx in self.sections[section_name]:
                hook_id, name, description, category, default = HOOKS[hook_idx]

                # Checkbox
                checkbox = "[X]" if self.enabled[hook_idx] else "[ ]"

                # Selection indicator
                indicator = ">" if current_item == self.selected_index else " "

                # Display line
                print(f"{indicator} {checkbox} {name}")

                current_item += 1

            print()

        # Footer
        enabled_count = sum(1 for e in self.enabled.values() if e)
        print(f"Hooks selected: {enabled_count}/{len(HOOKS)}")

        # Show description of currently selected hook
        if self.selected_index < len(HOOKS):
            current_hook_idx = self._get_item_at_index(self.selected_index)
            if current_hook_idx is not None:
                _, _, description, _, _ = HOOKS[current_hook_idx]
                print()
                print(f"Description: {description}")

        if self.message:
            print()
            print(f">>> {self.message}")

    def _get_key(self):
        """Get a single keypress from the user."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)

            # Handle arrow keys (they send escape sequences)
            if key == '\x1b':
                next_chars = sys.stdin.read(2)
                if next_chars == '[A':  # Up arrow
                    key = 'UP'
                elif next_chars == '[B':  # Down arrow
                    key = 'DOWN'

            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _get_item_at_index(self, idx):
        """Get the hook index for the given selection index."""
        current = 0
        for section_name in ["security", "quality", "productivity", "control"]:
            for hook_idx in self.sections[section_name]:
                if current == idx:
                    return hook_idx
                current += 1
        return None

    def _get_total_items(self):
        """Get total number of selectable items."""
        return len(HOOKS)

    def run(self):
        """Main UI loop."""
        total_items = self._get_total_items()

        while True:
            self._display_menu()
            key = self._get_key()

            if key in ['q', 'Q', '\x03']:  # q or Ctrl+C
                print("\nConfiguration cancelled.")
                return None

            elif key in ['UP', 'w', 'W']:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    self.message = ""

            elif key in ['DOWN', 's', 'S']:
                if self.selected_index < total_items - 1:
                    self.selected_index += 1
                    self.message = ""

            elif key == ' ':  # Space to toggle
                hook_idx = self._get_item_at_index(self.selected_index)
                if hook_idx is not None:
                    self.enabled[hook_idx] = not self.enabled[hook_idx]
                    hook_id, name, description, category, default = HOOKS[hook_idx]
                    state = "enabled" if self.enabled[hook_idx] else "disabled"
                    self.message = f"{name} {state}"

            elif key in ['a', 'A']:  # Select all
                for i in self.enabled:
                    self.enabled[i] = True
                self.message = "All hooks enabled"

            elif key in ['\r', '\n']:  # Enter to confirm
                self._clear_screen()
                return self._get_selected_hooks()

    def _get_selected_hooks(self):
        """Get list of selected hooks."""
        selected_hooks = []

        for i, (hook_id, name, description, category, default) in enumerate(HOOKS):
            if self.enabled.get(i, False):
                selected_hooks.append({
                    "id": hook_id,
                    "name": name,
                    "description": description,
                    "category": category
                })

        return selected_hooks

def save_hook_selection(hooks, hooks_dir):
    """Save selected hooks to configuration file"""
    config_file = Path(hooks_dir) / "hooks-installed.json"

    config = {
        "version": "1.0.0",
        "installed_hooks": [h["id"] for h in hooks],
        "hooks": {h["id"]: h for h in hooks}
    }

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config_file

def main():
    # Check for developer mode flag
    developer_mode = "--developer" in sys.argv

    if developer_mode:
        print("Developer Mode: Selecting all hooks by default")
    else:
        print("Configuring Claude Code hooks...")
    print()

    # Get hooks directory
    hooks_dir = Path(__file__).parent

    # Show interactive menu
    configurator = HookConfigurator(developer_mode)
    selected_hooks = configurator.run()

    if selected_hooks is None:
        sys.exit(0)

    # Save configuration
    config_file = save_hook_selection(selected_hooks, hooks_dir)

    print()
    print(f"Hook configuration saved to {config_file}")
    print(f"Selected {len(selected_hooks)} hooks")
    print()

    # Group by category
    by_category = {}
    for hook in selected_hooks:
        cat = hook["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(hook)

    # Display selected hooks by category
    for cat_id in ["security", "quality", "productivity", "control"]:
        if cat_id in by_category:
            print(f"{CATEGORIES[cat_id]}:")
            for hook in by_category[cat_id]:
                print(f"  • {hook['name']}")
            print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
