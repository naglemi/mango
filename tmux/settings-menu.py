#!/usr/bin/env python3
"""
Settings Menu for Tmux Integration
Provides interface to toggle Python error handler and other settings
"""

import json
import os
import shutil
import sys
import termios
import tty
from pathlib import Path
from typing import Dict, Any

class SettingsMenu:
    """Interactive settings menu for tmux integration."""

    def __init__(self):
        self.settings_file = Path.home() / ".claude" / "settings.json"
        self.bashrc_file = Path.home() / ".bashrc"
        self.settings = self._load_settings()
        self.menu_items = [
            {
                "key": "python_error_handler_enabled",
                "name": "Python Error Handler",
                "description": "Capture Python errors with code context",
                "type": "bool"
            },
            {
                "key": "report_folder_mode",
                "name": "Report MCP Mode",
                "description": "LOCAL: Save to ~/reports | EMAIL: Use S3/SES cloud",
                "type": "choice",
                "choices": ["EMAIL", "LOCAL"]
            },
            {
                "key": "blog_mode",
                "name": "Blog Workflow Mode",
                "description": "REPO: Blog repo | FOLDER: Local folder | SKIP: Not configured",
                "type": "choice",
                "choices": ["SKIP", "REPO", "FOLDER"]
            },
            {
                "key": "blog_path",
                "name": "Blog Path",
                "description": "Path to blog repo or output folder",
                "type": "text"
            },
            {
                "key": "blog_notebooks_dir",
                "name": "Blog Notebooks Directory",
                "description": "Subdirectory for notebooks (repo mode only)",
                "type": "text",
                "default": "_notebooks"
            },
            {
                "key": "blog_reports_dir",
                "name": "Blog Reports Directory",
                "description": "Subdirectory for reports (repo mode only)",
                "type": "text",
                "default": "_reports"
            },
            {
                "key": "tmux_color_notifications_enabled",
                "name": "Tmux Pane Color Notifications",
                "description": "Change pane color when Claude is idle (green) vs active (default)",
                "type": "bool"
            },
            {
                "key": "tmux_idle_color",
                "name": "Tmux Idle Color",
                "description": "Pane background when Claude finishes responding",
                "type": "choice",
                "choices": ["green", "cyan", "blue", "magenta", "yellow", "black", "default"]
            },
            {
                "key": "tmux_active_color",
                "name": "Tmux Active Color",
                "description": "Pane background when Claude is processing",
                "type": "choice",
                "choices": ["default", "green", "cyan", "blue", "magenta", "yellow", "black"]
            },
            {
                "key": "custom_status_line_enabled",
                "name": "Custom Status Line",
                "description": "Show hostname, directory, and git branch in status line",
                "type": "bool"
            },
            {
                "key": "status_line_update_interval",
                "name": "Status Line Update Interval",
                "description": "How often to update status line (seconds)",
                "type": "choice",
                "choices": ["5", "10", "30", "60"]
            },
            {
                "key": "skip_close_pane_confirmation",
                "name": "Skip Close Pane Confirmation",
                "description": "Close pane immediately without confirmation menu (Ctrl+X)",
                "type": "bool"
            }
        ]
        self.current_index = 0

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_settings(self):
        """Save settings to file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Handle status line configuration
            if self.settings.get("custom_status_line_enabled", False):
                self._setup_status_line()
            else:
                # Remove status line configuration if disabled
                if "statusLine" in self.settings:
                    del self.settings["statusLine"]

            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _setup_status_line(self):
        """Setup status line script and configuration."""
        try:
            # Copy template to ~/.claude/statusline.sh
            template_path = Path(__file__).parent / "statusline-template.sh"
            statusline_path = Path.home() / ".claude" / "statusline.sh"

            if template_path.exists():
                shutil.copy(template_path, statusline_path)
                statusline_path.chmod(0o755)  # Make executable

            # Add status line configuration to settings
            interval = self.settings.get("status_line_update_interval", "30")
            self.settings["statusLine"] = {
                "type": "command",
                "command": str(statusline_path),
                "padding": 0,
                "updateIntervalSeconds": int(interval)
            }
        except Exception as e:
            print(f"Warning: Could not setup status line: {e}")

    def _update_bashrc(self):
        """Update bashrc with current settings."""
        try:
            if not self.bashrc_file.exists():
                return

            # Read current bashrc
            with open(self.bashrc_file, 'r') as f:
                lines = f.readlines()

            # Update USABILIDE_REPORT_FOLDER based on report_folder_mode setting
            report_mode = self.settings.get("report_folder_mode", "EMAIL")
            if report_mode == "LOCAL":
                report_folder_value = f'"{Path.home()}/reports"'
            else:
                report_folder_value = '"EMAIL"'

            # Find and update or add the export line
            found_report = False
            for i, line in enumerate(lines):
                if line.strip().startswith('export USABILIDE_REPORT_FOLDER='):
                    lines[i] = f'export USABILIDE_REPORT_FOLDER={report_folder_value}  # Change to folder path for local mode\n'
                    found_report = True
                    break

            if not found_report:
                # Add it after the PATH export
                for i, line in enumerate(lines):
                    if 'export PATH="$PATH:$HOME/mango"' in line:
                        # Insert after this line
                        lines.insert(i + 1, f'\n# Report MCP Configuration\n')
                        lines.insert(i + 2, f'# Options: Set to a folder path for local storage (e.g., "$HOME/reports")\n')
                        lines.insert(i + 3, f'#          Set to "EMAIL" or leave unset for S3/SES cloud mode\n')
                        lines.insert(i + 4, f'export USABILIDE_REPORT_FOLDER={report_folder_value}  # Change to folder path for local mode\n')
                        break

            # Update blog configuration
            blog_mode = self.settings.get("blog_mode", "SKIP")
            blog_path = self.settings.get("blog_path", "")
            blog_notebooks = self.settings.get("blog_notebooks_dir", "_notebooks")
            blog_reports = self.settings.get("blog_reports_dir", "_reports")

            # Remove old blog config
            new_lines = []
            skip_until_blank = False
            for line in lines:
                if line.strip() == "# Blog Configuration":
                    skip_until_blank = True
                    continue
                if skip_until_blank:
                    if line.strip() == "":
                        skip_until_blank = False
                    continue
                new_lines.append(line)

            lines = new_lines

            # Add new blog config if not SKIP
            if blog_mode != "SKIP":
                # Find a good place to add it (after Report MCP config or at end)
                insert_pos = len(lines)
                for i, line in enumerate(lines):
                    if 'USABILIDE_REPORT_FOLDER' in line:
                        # Find next blank line after this
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == "":
                                insert_pos = j + 1
                                break
                        break

                blog_config = [
                    "\n",
                    "# Blog Configuration\n",
                    f'export BLOG_MODE="{blog_mode}"\n',
                    f'export BLOG_PATH="{blog_path}"\n',
                    f'export BLOG_NOTEBOOKS_DIR="{blog_notebooks}"\n',
                    f'export BLOG_REPORTS_DIR="{blog_reports}"\n',
                ]

                for j, config_line in enumerate(blog_config):
                    lines.insert(insert_pos + j, config_line)

            # Write back
            with open(self.bashrc_file, 'w') as f:
                f.writelines(lines)

        except Exception as e:
            print(f"Warning: Could not update bashrc: {e}")

    def _regenerate_tmux_conf(self):
        """Regenerate tmux.conf if tmux settings changed."""
        # Check if tmux menu config exists (needed for generation)
        menu_config_file = Path.home() / ".tmux-menu-config.txt"
        if not menu_config_file.exists():
            # Menu not configured yet, skip regeneration
            return

        # Regenerate tmux.conf to apply close pane confirmation setting
        try:
            generate_script = Path(__file__).parent / "generate-tmux-conf.sh"
            if generate_script.exists():
                import subprocess
                subprocess.run([str(generate_script)], check=False, capture_output=True)
        except Exception:
            # Ignore errors - config will be regenerated on next menu configure
            pass

    def _clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def _display_menu(self):
        """Display the settings menu."""
        self._clear_screen()

        print("  Settings Menu")
        print("=" * 70)
        print("Controls: ↑↓ navigate, SPACE toggle/cycle, 'e' edit text, ENTER save, q quit")
        print("=" * 70)
        print()

        for i, item in enumerate(self.menu_items):
            key = item["key"]
            name = item["name"]
            description = item["description"]
            item_type = item.get("type", "bool")

            # Get current value and format status
            if item_type == "bool":
                current_value = self.settings.get(key, False)
                status = " ON" if current_value else " OFF"
            elif item_type == "choice":
                choices = item.get("choices", [])
                current_value = self.settings.get(key, choices[0] if choices else "")
                status = f"[{current_value}]"
            elif item_type == "text":
                default_value = item.get("default", "")
                current_value = self.settings.get(key, default_value)
                display_value = current_value if current_value else "(not set)"
                status = f"[{display_value}]"
            else:
                current_value = self.settings.get(key, "")
                status = f"[{current_value}]"

            # Highlight current selection
            if i == self.current_index:
                print(f"> {status} {name}")
                print(f"    {description}")
            else:
                print(f"  {status} {name}")
                print(f"    {description}")
            print()

        print("=" * 60)
        print("Settings file:", self.settings_file)

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
            self.current_index = min(len(self.menu_items) - 1, self.current_index + 1)

        elif key == ' ':  # Space - toggle/cycle setting
            if self.menu_items:
                item = self.menu_items[self.current_index]
                item_key = item["key"]
                item_type = item.get("type", "bool")

                if item_type == "bool":
                    current_value = self.settings.get(item_key, False)
                    self.settings[item_key] = not current_value
                elif item_type == "choice":
                    choices = item.get("choices", [])
                    if choices:
                        current_value = self.settings.get(item_key, choices[0])
                        try:
                            current_idx = choices.index(current_value)
                            next_idx = (current_idx + 1) % len(choices)
                            self.settings[item_key] = choices[next_idx]
                        except ValueError:
                            self.settings[item_key] = choices[0]
                elif item_type == "text":
                    # For text items, space does nothing (use 'e' to edit)
                    pass

        elif key in ['e', 'E']:  # Edit text field
            if self.menu_items:
                item = self.menu_items[self.current_index]
                item_key = item["key"]
                item_type = item.get("type", "bool")

                if item_type == "text":
                    # Enter edit mode for text field
                    default_value = item.get("default", "")
                    current_value = self.settings.get(item_key, default_value)

                    # Restore terminal to normal mode for input
                    self._clear_screen()
                    print(f"Editing: {item['name']}")
                    print(f"Current: {current_value if current_value else '(not set)'}")
                    print()

                    # Get user input (need to restore terminal mode)
                    import sys
                    import termios
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        # Restore normal terminal mode
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        new_value = input(f"New value (or Enter to keep current): ").strip()

                        # Expand ~ to home directory
                        if new_value and new_value.startswith('~'):
                            new_value = str(Path.home()) + new_value[1:]

                        if new_value:
                            self.settings[item_key] = new_value
                    finally:
                        pass  # Will go back to raw mode on next loop

        elif key == '\r' or key == '\n':  # Enter - save and exit
            self._save_settings()
            self._update_bashrc()
            self._regenerate_tmux_conf()
            return False

        return True

    def run_menu(self):
        """Run the interactive settings menu."""
        try:
            while True:
                self._display_menu()
                key = self._get_char()

                if not self._handle_input(key):
                    break

        except KeyboardInterrupt:
            print("\nSettings not saved.")
            return

        # Clear screen and show final status
        self._clear_screen()
        print("  Settings Saved")
        print("=" * 50)
        for item in self.menu_items:
            key = item["key"]
            name = item["name"]
            item_type = item.get("type", "bool")

            if item_type == "bool":
                current_value = self.settings.get(key, False)
                status = " ON" if current_value else " OFF"
            elif item_type == "choice":
                current_value = self.settings.get(key, item.get("choices", [""])[0])
                status = f"[{current_value}]"
            else:
                current_value = self.settings.get(key, "")
                status = f"[{current_value}]"

            print(f"{status} {name}")
        print()
        print("Changes applied:")
        if self.settings.get("report_folder_mode") == "LOCAL":
            print("  • Report MCP: Using local folder ~/reports")
            print("  • Run 'source ~/.bashrc' to apply")
        else:
            print("  • Report MCP: Using S3/SES cloud mode")
            print("  • Run 'source ~/.bashrc' to apply")

        blog_mode = self.settings.get("blog_mode", "SKIP")
        if blog_mode != "SKIP":
            blog_path = self.settings.get("blog_path", "")
            print(f"  • Blog Workflow: {blog_mode} mode")
            if blog_path:
                print(f"    Path: {blog_path}")
            print("  • Run 'source ~/.bashrc' to apply")
        print()

def main():
    """Main entry point."""
    try:
        menu = SettingsMenu()
        menu.run_menu()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()