#!/usr/bin/env python3
"""
Interactive Hook Selector for Claude Code
Provides a checkbox menu to enable/disable hooks in ~/.claude/settings.json
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from hook_manager import HookManager


class InteractiveHookSelector:
    """Interactive terminal menu for selecting and managing Claude Code hooks."""
    
    def __init__(self):
        # Paths
        self.script_dir = Path(__file__).parent.resolve()
        self.registry_path = self.script_dir / "hook_registry.json"
        self.messages_path = self.script_dir / "hook_messages.json"
        self.global_settings = Path.home() / ".claude" / "settings.json"
        
        # Load registry
        self.registry = self._load_registry()
        self.hooks_list = sorted(
            self.registry["hooks"].items(),
            key=lambda x: x[1].get("name", x[0]).lower()
        )
        
        # Load messages
        self.messages = self._load_messages()
        
        # Load current hooks
        self.manager = HookManager(str(self.global_settings))
        self.enabled_hooks = self._get_enabled_hooks()
        
        # UI state
        self.selected_index = 0
        
    def _load_registry(self) -> Dict:
        """Load the hook registry."""
        with open(self.registry_path, 'r') as f:
            return json.load(f)
    
    def _load_messages(self) -> Dict:
        """Load hook messages."""
        if self.messages_path.exists():
            with open(self.messages_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_messages(self):
        """Save hook messages."""
        with open(self.messages_path, 'w') as f:
            json.dump(self.messages, f, indent=2)
    
    def _get_enabled_hooks(self) -> Set[str]:
        """Get set of currently enabled hook IDs."""
        enabled = set()
        current_hooks = self.manager.list_hooks()
        
        for event, matchers in current_hooks.items():
            for matcher_config in matchers:
                if "hooks" in matcher_config:
                    for hook in matcher_config["hooks"]:
                        command = hook.get("command", "")
                        # Extract hook ID from command path
                        for hook_id, hook_info in self.registry["hooks"].items():
                            script_name = hook_info.get("script", "")
                            if script_name and f"/{script_name}" in command:
                                # Use /script_name to ensure exact match, not substring
                                enabled.add(hook_id)
                                break
        
        return enabled
    
    def _get_global_script_path(self, hook_id: str) -> str:
        """Get the absolute path for a hook script in global installation."""
        hook_info = self.registry["hooks"].get(hook_id, {})
        script_name = hook_info.get("script", "")
        if script_name:
            return str(self.script_dir / script_name)
        return ""
    
    def _toggle_hook(self, hook_id: str) -> str:
        """Toggle a hook on/off."""
        hook_info = self.registry["hooks"].get(hook_id)
        if not hook_info:
            return "Hook not found in registry"
        
        # Check if compatible with global installation
        if "global" not in hook_info.get("compatible_with", []):
            return f"Hook '{hook_id}' is not compatible with global installation"
        
        if hook_id in self.enabled_hooks:
            # Remove the hook
            script_path = self._get_global_script_path(hook_id)
            success = self.manager.remove_hook(
                event=hook_info["event"],
                matcher=hook_info.get("matcher", ""),
                command=script_path
            )
            
            if success:
                self.enabled_hooks.discard(hook_id)
                return f"Disabled: {hook_info['name']}"
            else:
                return f"Failed to disable: {hook_info['name']}"
        else:
            # Add the hook
            script_path = self._get_global_script_path(hook_id)
            
            # Check if script exists
            if not Path(script_path).exists():
                return f"Script not found: {script_path}"
            
            success = self.manager.add_hook(
                event=hook_info["event"],
                matcher=hook_info.get("matcher", ""),
                command=script_path,
                timeout=hook_info.get("timeout"),
                description=hook_info.get("description")
            )
            
            if success:
                self.enabled_hooks.add(hook_id)
                return f"Enabled: {hook_info['name']}"
            else:
                return f"Failed to enable: {hook_info['name']}"
    
    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def _display_menu(self, message=""):
        """Display the hook selection menu."""
        self._clear_screen()

        # Header
        output_level = self.manager.get_output_level()
        print(f"[C] Config | [M] Message | [D] Details | [O] Output:{output_level} | [I] Discuss | [K] Kill | [Q] Quit")
        print()

        # Display hooks
        for i, (hook_id, hook_info) in enumerate(self.hooks_list):
            # Check if compatible
            is_compatible = "global" in hook_info.get("compatible_with", [])
            is_enabled = hook_id in self.enabled_hooks
            is_selected = i == self.selected_index
            
            # Build display line
            if not is_compatible:
                checkbox = "[-]"
                status = "(incompatible)"
            elif hook_info.get("configurable"):
                if is_enabled:
                    config_var = hook_info.get("config_var")
                    config_value = os.environ.get(config_var, "") if config_var else ""
                    if config_value:
                        checkbox = f"[{config_value}]"
                    else:
                        checkbox = "[X]"
                else:
                    checkbox = "[ ]"
                status = ""
            else:
                checkbox = "[X]" if is_enabled else "[ ]"
                status = ""
            
            name = hook_info.get("name", hook_id)[:30]
            desc = hook_info.get("description", "")[:40]
            
            # Selection indicator
            indicator = ">" if is_selected else " "
            
            print(f"{indicator} {checkbox} {name:<32} {desc} {status}")
        
        # Footer
        print()
        print(f"Enabled: {len(self.enabled_hooks)} hooks")
        print()
    
    def _configure_hook(self, hook_id: str, hook_info: Dict) -> str:
        """Configure a hook's environment variable."""
        config_var = hook_info.get("config_var")
        config_desc = hook_info.get("config_desc", "")
        
        if not config_var:
            return "No configuration variable defined"
        
        # Clear screen and show configuration prompt
        self._clear_screen()
        print(f"Configure: {hook_info.get('name', hook_id)}")
        print()
        print(f"Environment Variable: {config_var}")
        print(f"Description: {config_desc}")
        print()
        
        current_value = os.environ.get(config_var, "")
        print(f"Current value: {current_value or '(not set)'}")
        print()
        
        # Get new value from user
        print("Enter new value (or press Enter to keep current, 'clear' to unset):")
        
        # Restore normal terminal mode for input
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        try:
            new_value = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            return "Configuration cancelled"
        
        if new_value.lower() == 'clear':
            # Remove from bashrc
            self._update_bashrc_var(config_var, None)
            return f"Cleared {config_var}"
        elif new_value:
            # Update bashrc with new value
            self._update_bashrc_var(config_var, new_value)
            os.environ[config_var] = new_value
            return f"Set {config_var}={new_value}"
        else:
            return "No changes made"
    
    def _edit_message(self, hook_id: str, hook_info: Dict) -> str:
        """Edit the message shown when a hook is triggered."""
        # Clear screen and show message editing prompt
        self._clear_screen()
        print(f"Edit Message: {hook_info.get('name', hook_id)}")
        print()
        
        current_message = self.messages.get(hook_id, "Hook triggered - action blocked.")
        print(f"Current message:")
        print(f"  {current_message}")
        print()
        print("Enter new message (or press Enter to keep current):")
        
        # Restore normal terminal mode for input
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        try:
            new_message = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            return "Message edit cancelled"
        
        if new_message:
            self.messages[hook_id] = new_message
            self._save_messages()
            return "Message updated"
        else:
            return "No changes made"
    
    def _update_bashrc_var(self, var_name: str, value: str):
        """Update or remove an environment variable in ~/.bashrc."""
        bashrc_path = Path.home() / ".bashrc"
        
        if not bashrc_path.exists():
            if value:
                with open(bashrc_path, 'w') as f:
                    f.write(f"export {var_name}={value}\n")
            return
        
        # Read existing bashrc
        with open(bashrc_path, 'r') as f:
            lines = f.readlines()
        
        # Find and update/remove the variable
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"export {var_name}="):
                if value:
                    new_lines.append(f"export {var_name}={value}\n")
                    updated = True
                # Skip line if clearing
            else:
                new_lines.append(line)
        
        # Add if not found and value provided
        if not updated and value:
            new_lines.append(f"export {var_name}={value}\n")
        
        # Write back
        with open(bashrc_path, 'w') as f:
            f.writelines(new_lines)
    
    def _show_details(self, hook_id: str):
        """Show detailed information about a hook."""
        self._clear_screen()
        hook_info = self.registry["hooks"].get(hook_id, {})
        
        print(f"{hook_info.get('name', hook_id)}")
        print()
        
        print(f"ID: {hook_id}")
        print(f"Description: {hook_info.get('description', 'No description')}")
        print(f"Event: {hook_info.get('event', 'Unknown')}")
        print(f"Matcher: {hook_info.get('matcher', 'N/A') or 'N/A'}")
        print(f"Timeout: {hook_info.get('timeout', 'Default')} seconds")
        print(f"Script: {hook_info.get('script', 'Unknown')}")
        print(f"Tags: {', '.join(hook_info.get('tags', []))}")
        print(f"Compatible with: {', '.join(hook_info.get('compatible_with', []))}")
        
        deps = hook_info.get('dependencies', [])
        if deps:
            print(f"Dependencies: {', '.join(deps)}")
        
        print()
        print("Press any key to return...")
        self._get_key()
    
    def _get_key(self):
        """Get a single keypress from the user."""
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        
        # Handle arrow keys (they send escape sequences)
        if key == '\x1b':
            key += sys.stdin.read(2)
            if key == '\x1b[A':  # Up arrow
                key = 'UP'
            elif key == '\x1b[B':  # Down arrow
                key = 'DOWN'
        
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        return key
    
    def run(self):
        """Main UI loop."""
        message = ""
        
        while True:
            self._display_menu(message)
            key = self._get_key()
            
            if key in ['q', 'Q', '\x03']:  # q or Ctrl+C
                break
            
            elif key in ['UP', 'w', 'W']:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    message = ""
            
            elif key in ['DOWN', 's', 'S']:
                if self.selected_index < len(self.hooks_list) - 1:
                    self.selected_index += 1
                    message = ""
            
            elif key == ' ':  # Space to toggle
                if self.selected_index < len(self.hooks_list):
                    hook_id, hook_info = self.hooks_list[self.selected_index]
                    message = self._toggle_hook(hook_id)
            
            elif key in ['c', 'C']:
                if self.selected_index < len(self.hooks_list):
                    hook_id, hook_info = self.hooks_list[self.selected_index]
                    if hook_info.get("configurable"):
                        message = self._configure_hook(hook_id, hook_info)
                    else:
                        message = "This hook is not configurable"
            
            elif key in ['m', 'M']:
                if self.selected_index < len(self.hooks_list):
                    hook_id, hook_info = self.hooks_list[self.selected_index]
                    message = self._edit_message(hook_id, hook_info)
            
            elif key in ['d', 'D']:
                if self.selected_index < len(self.hooks_list):
                    hook_id, _ = self.hooks_list[self.selected_index]
                    self._show_details(hook_id)
                    message = ""
            
            elif key in ['i', 'I']:  # Discuss - launch Claude
                import subprocess
                import os
                
                # Save current directory and change to hooks folder
                original_dir = os.getcwd()
                os.chdir(self.script_dir)
                
                # Check if there's an existing conversation
                claude_history = Path(self.script_dir) / '.claude' / 'claude.md'
                if claude_history.exists():
                    # Continue existing conversation
                    subprocess.run(['claude', '--dangerously-skip-permissions', '--continue'])
                else:
                    # Start new conversation
                    subprocess.run(['claude', '--dangerously-skip-permissions'])
                
                # Return to original directory
                os.chdir(original_dir)
                message = ""
            
            elif key in ['o', 'O']:  # Toggle output level
                current_level = self.manager.get_output_level()
                # Cycle through: silent -> error -> all -> silent
                level_cycle = {"silent": "error", "error": "all", "all": "silent"}
                new_level = level_cycle.get(current_level, "silent")

                if self.manager.set_output_level(new_level):
                    message = f"Hook output level set to: {new_level}"
                else:
                    message = "Failed to change output level"

            elif key in ['k', 'K']:  # Kill zombie hook processes
                import subprocess
                try:
                    result = subprocess.run(['sudo', 'pkill', '-f', 'hook'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        message = "Killed zombie hook processes"
                    else:
                        message = "No hook processes found to kill"
                except Exception as e:
                    message = f"Failed to kill hooks: {str(e)}"
            
    
    def print_summary(self):
        """Print summary after exiting."""
        pass  # Silent exit


def main():
    """Main entry point."""
    # Check if running in terminal
    if not sys.stdout.isatty():
        print("Error: This tool requires an interactive terminal")
        sys.exit(1)
    
    # Check for required termios module
    import termios
    
    selector = InteractiveHookSelector()
    selector.run()
    selector.print_summary()


if __name__ == "__main__":
    main()