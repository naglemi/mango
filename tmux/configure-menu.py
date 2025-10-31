#!/usr/bin/env python3
"""
Interactive menu configurator for tmux
Allows users to select which items appear in the Ctrl+G / right-click menu
"""

import os
import sys
import termios
import tty
from pathlib import Path

# Menu items with their configuration
# Format: (display_name, key_binding, command, is_core, default_enabled, section, description)
MENU_ITEMS = [
    # Core window/pane management (always enabled, not selectable)
    ("🆕 New Window", "n", "new-window", True, True, "core", "Creates a new tmux window in the current session. Windows function like browser tabs."),
    ("👉 Next Window", "s", "next-window", True, True, "core", "Switches to the next window in the window list. Cycles back to first window after last."),
    ("💥 Break to Window", "d", "break-pane", True, True, "core", "Breaks current pane into a separate window. The pane becomes window #N where N is next available."),
    ("📦 Consolidate Windows", "W", "display-popup -E -w 90% -h 90% '\$HOME/mango/tmux/consolidate-windows.sh'", True, True, "core", "Merges all windows into panes within a single window. Opens interactive selector for window consolidation."),
    ("❌ Close Pane", "z", "{{CLOSE_PANE_CMD}}", True, True, "core", "Close current pane (respects skip_close_pane_confirmation setting in Settings menu)."),
    ("📛 Rename Window", "R", "command-prompt -I '#W' 'rename-window \"%%\"'", True, True, "core", "Rename the current window. Window names appear in the status bar tabs."),
    ("📥 Split Horizontal", "h", "split-window -v -c '#{pane_current_path}'", True, True, "core", "Splits current pane into top and bottom halves. New pane starts in same working directory."),
    ("🔀 Split Vertical", "v", "split-window -h -c '#{pane_current_path}'", True, True, "core", "Splits current pane into left and right halves. New pane starts in same working directory."),

    # Basic features (enabled by default)
    ("📝 Neovim", "e", "split-window -h -c '#{pane_current_path}' 'nvim'", False, True, "basic", "Opens Neovim text editor in new pane. Starts in current working directory."),
    ("🌿 Lazygit", "c", "split-window -h -c '#{pane_current_path}' 'lazygit'", False, True, "basic", "Launches lazygit terminal UI. Provides git staging, commits, branches, and history navigation."),
    ("🔱 Fork Claude", "f", "split-window -h -c '#{pane_current_path}' 'claude --continue --dangerously-skip-permissions'", False, True, "basic", "Starts new Claude Code session continuing from current conversation context. Skips permission prompts."),
    ("🎣 Hook Manager", "p", "split-window -h -c '#{pane_current_path}' 'python3 \$HOME/mango/hooks/configure-hooks.py'", False, True, "basic", "Opens interactive hooks configuration interface. Enable/disable/configure Claude Code event hooks."),
    ("📄 CLAUDE.md", "o", "split-window -h -c '#{pane_current_path}' '\$HOME/mango/tmux/claude-md-split.sh'", False, True, "basic", "Opens CLAUDE.md file in current directory with vim. Creates file if it doesn't exist."),
    ("📊 System Monitor", "t", "split-window -h '\$HOME/mango/tmux/htop-split.sh'", False, True, "basic", "Opens htop in new pane. Displays processes, CPU cores, memory, swap, and load averages."),
    ("🔐 SSH to Host", "a", "split-window -h '\$HOME/mango/tmux/ssh-split.sh'", False, True, "basic", "Parses ~/.ssh/config for Host entries. Presents fzf menu to select and connect to hosts."),
    ("🔧 Settings", "w", "split-window -h -c '#{pane_current_path}' 'python3 \$HOME/mango/tmux/settings-menu.py'", False, True, "basic", "Interactive tmux configuration menu. Adjust mouse mode, status bar, key bindings, and other settings."),
    ("🔌 Plugin Manager", "P", "display-menu -T 'Plugin Manager' 'Session Tree (Ctrl+b Ctrl+w)' w 'send-keys C-b C-w' 'Save Session (Ctrl+b Ctrl+s)' s 'send-keys C-b C-s' 'Restore Session (Ctrl+b Ctrl+r)' r 'send-keys C-b C-r' 'Install Plugins (Ctrl+b I)' I 'send-keys C-b I' 'Update Plugins (Ctrl+b U)' U 'send-keys C-b U'", False, True, "basic", "Menu shortcuts for TPM (Tmux Plugin Manager). Manage resurrect, continuum, and other tmux plugins."),

    # Advanced features (disabled by default)
    ("👀 Glances Monitor", "l", "split-window -h '\$HOME/mango/tmux/glances-split.sh'", False, False, "advanced", "Opens glances system monitor. Shows CPU, memory, disk I/O, network, sensors, and Docker stats."),
    ("🤖 Train Model", "x", "split-window -h -c '#{pane_current_path}' 'python3 \$HOME/mango/tmux/training-menu.py'", False, False, "advanced", "ML training launcher for finetune projects. Auto-detects configs directory, starts training with main.py and logging."),
    ("📈 W&B Monitor", "m", "split-window -h -c '#{pane_current_path}' '\$HOME/mango/tmux/wandb-monitor.sh'", False, False, "advanced", "Monitor Weights & Biases runs. Auto-refreshing view of experiment metrics, system stats, and logs."),
    ("🎮 NVTOP Monitor", "q", "split-window -v -l 10 'nvtop'", False, False, "advanced", "Opens nvtop GPU monitor in bottom pane (10 lines). Shows per-GPU utilization, memory, temp, and process list."),
    ("💾 GPUstat Compact", "u", "split-window -v -l 8 'watch -n 1 gpustat -cp'", False, False, "advanced", "Compact GPU status in bottom pane (8 lines). Updates every 1 second with GPU stats and processes."),
    ("🌐 EC2 SSH", "b", "split-window -h -c '#{pane_current_path}' '\$HOME/mango/tmux/ec2-ssh-menu.sh'", False, False, "advanced", "Queries AWS API for running EC2 instances. Select instance to SSH using instance metadata and key."),
    ("💼 SLURM Jobs", "j", "split-window -h '\$HOME/mango/tmux/slurm-job-split.sh'", False, False, "advanced", "Interface for SLURM workload manager. View queue, submit jobs, check status, and cancel running jobs."),
    ("🔍 Spectator", "i", "split-window -h -c '#{pane_current_path}' '\$HOME/mango/tmux/spectator.sh #{pane_current_path}'", False, False, "advanced", "Watch files change in real-time. Shows git-modified files, opens in read-only vim with auto-reload for monitoring agent edits."),

    # Beta features
    ("💬 Ask LLM", "k", "split-window -h -c '#{pane_current_path}' '\$HOME/mango/tmux/ask-llm.sh'", False, False, "beta", "Interactive LLM query tool. Select files as context, choose AI models, compare responses side-by-side or sequential."),
]

class MenuConfigurator:
    """Interactive menu configurator using custom TUI."""

    def __init__(self):
        # Group items by section
        self.sections = {
            "basic": [],
            "advanced": [],
            "beta": []
        }

        # Initialize enabled state with defaults
        self.enabled = {}

        for i, (name, key, cmd, is_core, default, section, description) in enumerate(MENU_ITEMS):
            if not is_core:
                self.sections[section].append(i)
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
        print("TMUX MENU CONFIGURATOR")
        print("=" * 70)
        print("Use ↑/↓ or W/S to navigate | Space to toggle | A to select all | Enter to confirm | Q to cancel")
        print()

        current_item = 0

        # Display sections
        for section_name in ["basic", "advanced", "beta"]:
            section_title = {
                "basic": "BASIC (included by default)",
                "advanced": "ADVANCED (not included by default)",
                "beta": "BETA (experimental features)"
            }[section_name]

            print(f"=== {section_title} ===")
            print()

            for item_idx in self.sections[section_name]:
                name, key, cmd, is_core, default, section, description = MENU_ITEMS[item_idx]

                # Checkbox
                checkbox = "[X]" if self.enabled[item_idx] else "[ ]"

                # Selection indicator
                indicator = ">" if current_item == self.selected_index else " "

                # Display line
                print(f"{indicator} {checkbox} {name}")

                current_item += 1

            print()

        # Core items note
        print("Core items (always included):")
        for name, key, cmd, is_core, default, section, description in MENU_ITEMS:
            if is_core:
                print(f"  • {name}")

        # Footer
        enabled_count = sum(1 for e in self.enabled.values() if e)
        print()
        print(f"Optional items selected: {enabled_count}")

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
        """Get the menu item index for the given selection index."""
        current = 0
        for section_name in ["basic", "advanced", "beta"]:
            for item_idx in self.sections[section_name]:
                if current == idx:
                    return item_idx
                current += 1
        return None

    def _get_total_items(self):
        """Get total number of selectable items."""
        return sum(len(items) for items in self.sections.values())

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
                item_idx = self._get_item_at_index(self.selected_index)
                if item_idx is not None:
                    self.enabled[item_idx] = not self.enabled[item_idx]
                    name = MENU_ITEMS[item_idx][0]
                    state = "enabled" if self.enabled[item_idx] else "disabled"
                    self.message = f"{name} {state}"

            elif key in ['a', 'A']:  # Select all
                for i in self.enabled:
                    self.enabled[i] = True
                self.message = "All items enabled"

            elif key in ['\r', '\n']:  # Enter to confirm
                self._clear_screen()
                return self._get_selected_items()

    def _get_selected_items(self):
        """Get list of selected menu items."""
        enabled_items = []

        # Always include core items first
        for i, (name, key, cmd, is_core, default, section, description) in enumerate(MENU_ITEMS):
            if is_core:
                enabled_items.append((name, key, cmd, True))  # True = is_core

        # Add selected non-core items
        for i, (name, key, cmd, is_core, default, section, description) in enumerate(MENU_ITEMS):
            if not is_core and self.enabled.get(i, False):
                enabled_items.append((name, key, cmd, False))  # False = not core

        return enabled_items

def generate_menu_config(items):
    """Generate the display-menu configuration lines"""
    lines = []
    prev_was_core = None

    for i, (name, key, cmd, is_core) in enumerate(items):
        # Add separator between core and non-core items
        if prev_was_core is True and is_core is False:
            lines.append('    "" \\')

        prev_was_core = is_core

        # Format menu item - backslash on all lines EXCEPT the very last one
        is_last_item = (i == len(items) - 1)
        if is_last_item:
            lines.append(f'    "{name:<20}" {key} "{cmd}"')
        else:
            lines.append(f'    "{name:<20}" {key} "{cmd}" \\')

    return lines

def main():
    print("  Configuring tmux menu items...")
    print()

    # Show interactive menu
    configurator = MenuConfigurator()
    selected_items = configurator.run()

    if selected_items is None:
        sys.exit(0)

    # Generate configuration
    menu_lines = generate_menu_config(selected_items)

    # Save configuration
    config_file = Path.home() / ".tmux-menu-config.txt"
    with open(config_file, 'w') as f:
        f.write('\n'.join(menu_lines))
        f.write('\n')  # Add trailing newline so last line is read properly

    print()
    print(f" Menu configuration saved to {config_file}")
    print(f" Selected {len([i for i in selected_items if not i[3]])} optional items")
    print()
    print("Core items (always included):")
    for name, key, cmd, is_core in selected_items:
        if is_core:
            print(f"  • {name}")

    print()
    print("Optional items (selected):")
    for name, key, cmd, is_core in selected_items:
        if not is_core:
            print(f"  • {name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
