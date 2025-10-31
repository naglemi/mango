#!/usr/bin/env python3
"""
Claude Code Hook Manager
Safely manage hooks in settings.json files without corruption
"""

import json
import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import fcntl
import tempfile


class HookManager:
    """Manages Claude Code hooks with safe JSON manipulation and backup."""

    def __init__(self, settings_path: str):
        self.settings_path = Path(settings_path)
        self.backup_dir = self.settings_path.parent / ".claude_backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Find hooks directory
        self.hooks_dir = Path(__file__).parent
        self.installed_hooks_file = self.hooks_dir / "hooks-installed.json"
        self.hook_registry_file = self.hooks_dir / "hook_registry.json"
        
    def _acquire_lock(self, file_handle):
        """Acquire exclusive lock on file to prevent concurrent modifications."""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            print("Warning: Could not acquire exclusive lock on settings file")
            return False
    
    def _release_lock(self, file_handle):
        """Release file lock."""
        try:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except:
            pass
    
    def _create_backup(self) -> Optional[Path]:
        """Create timestamped backup of current settings."""
        if not self.settings_path.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"settings_{timestamp}.json"
        
        try:
            shutil.copy2(self.settings_path, backup_path)
            print(f"Backup created: {backup_path}")
            
            # Keep only last 10 backups
            self._cleanup_old_backups()
            return backup_path
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backups, keeping only the most recent ones."""
        backups = sorted(self.backup_dir.glob("settings_*.json"))
        if len(backups) > keep_count:
            for backup in backups[:-keep_count]:
                backup.unlink()

    def _load_installed_hooks(self) -> Optional[Dict]:
        """Load the hooks-installed.json file created during installation."""
        if not self.installed_hooks_file.exists():
            return None

        try:
            with open(self.installed_hooks_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load installed hooks: {e}")
            return None

    def _load_hook_registry(self) -> Optional[Dict]:
        """Load the hook registry with metadata for all hooks."""
        if not self.hook_registry_file.exists():
            return None

        try:
            with open(self.hook_registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load hook registry: {e}")
            return None

    def _load_settings(self) -> Dict:
        """Load current settings or return empty structure."""
        if not self.settings_path.exists():
            return {}
        
        try:
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {self.settings_path}: {e}")
            print("Creating backup and starting fresh...")
            self._create_backup()
            return {}
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}
    
    def _save_settings(self, settings: Dict) -> bool:
        """Save settings atomically with validation."""
        # Validate JSON structure first
        try:
            json_str = json.dumps(settings, indent=2)
            json.loads(json_str)  # Validate it can be parsed back
        except (TypeError, ValueError) as e:
            print(f"Error: Invalid settings structure: {e}")
            return False
        
        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(dir=self.settings_path.parent, text=True)
        
        try:
            with os.fdopen(temp_fd, 'w') as f:
                if not self._acquire_lock(f):
                    print("Warning: Proceeding without exclusive lock")
                
                f.write(json_str)
                f.write('\n')  # Add trailing newline for cleaner files
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
                
                self._release_lock(f)
            
            # Atomically replace the original file
            Path(temp_path).replace(self.settings_path)
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            try:
                os.unlink(temp_path)
            except:
                pass
            return False
    
    def add_hook(self, event: str, matcher: str, command: str, 
                 timeout: Optional[int] = None, 
                 description: Optional[str] = None) -> bool:
        """Add a new hook to settings."""
        
        # Create backup first
        self._create_backup()
        
        # Load current settings
        settings = self._load_settings()
        
        # Ensure hooks structure exists
        if "hooks" not in settings:
            settings["hooks"] = {}
        
        if event not in settings["hooks"]:
            settings["hooks"][event] = []
        
        # Build new hook entry - ensure it's executable
        # If it's a Python script, prepend python (check which is available)
        if command.endswith('.py'):
            # Check which python command is available
            import subprocess
            try:
                subprocess.run(['python3', '--version'], capture_output=True, check=True)
                python_cmd = 'python3'
            except:
                python_cmd = 'python'  # Fall back to python
            actual_command = f"{python_cmd} {command}"
        else:
            actual_command = command
            
        new_hook = {
            "type": "command",
            "command": actual_command
        }
        
        if timeout:
            new_hook["timeout"] = timeout
        
        if description:
            new_hook["_description"] = description
        
        # Find or create matcher entry
        matcher_entry = None
        for entry in settings["hooks"][event]:
            if isinstance(entry, dict) and entry.get("matcher") == matcher:
                matcher_entry = entry
                break
        
        if not matcher_entry:
            # Create new matcher entry
            matcher_entry = {
                "matcher": matcher,
                "hooks": []
            }
            settings["hooks"][event].append(matcher_entry)
        
        # Check if hook already exists (handle both formats)
        possible_commands = [actual_command, command]
        if command.endswith('.py'):
            # Also check for alternative python commands
            possible_commands.extend([
                f"python {command}",
                f"python3 {command}"
            ])
        
        for existing_hook in matcher_entry.get("hooks", []):
            existing_cmd = existing_hook.get("command", "")
            if (existing_cmd in possible_commands or
                existing_cmd.endswith(command)):
                print(f"Hook already exists for {event}:{matcher} -> {command}")
                return False
        
        # Add the new hook
        if "hooks" not in matcher_entry:
            matcher_entry["hooks"] = []
        matcher_entry["hooks"].append(new_hook)
        
        # Save settings
        if self._save_settings(settings):
            print(f"Added hook: {event}:{matcher} -> {command}")
            return True
        else:
            print("Failed to save settings")
            return False
    
    def remove_hook(self, event: str, matcher: str, command: str) -> bool:
        """Remove a specific hook from settings."""
        
        # Create backup first
        self._create_backup()
        
        # Load current settings
        settings = self._load_settings()
        
        if "hooks" not in settings or event not in settings["hooks"]:
            print(f"No hooks found for event: {event}")
            return False
        
        # Find matcher entry
        for i, entry in enumerate(settings["hooks"][event]):
            if isinstance(entry, dict) and entry.get("matcher") == matcher:
                # Find and remove the hook
                hooks = entry.get("hooks", [])
                original_count = len(hooks)
                
                # Handle both direct path and python/python3 prefix formats
                possible_commands = [command]
                if command.endswith('.py'):
                    possible_commands.extend([
                        f"python {command}",
                        f"python3 {command}"
                    ])
                
                entry["hooks"] = [
                    h for h in hooks 
                    if h.get("command") not in possible_commands and
                       not h.get("command", "").endswith(command)
                ]
                
                if len(entry["hooks"]) < original_count:
                    # Hook was removed
                    if not entry["hooks"]:
                        # Remove empty matcher entry
                        settings["hooks"][event].pop(i)
                    
                    if not settings["hooks"][event]:
                        # Remove empty event entry
                        del settings["hooks"][event]
                    
                    if self._save_settings(settings):
                        print(f"Removed hook: {event}:{matcher} -> {command}")
                        return True
                    else:
                        print("Failed to save settings")
                        return False
        
        print(f"Hook not found: {event}:{matcher} -> {command}")
        return False
    
    def list_hooks(self) -> Dict:
        """List all configured hooks."""
        settings = self._load_settings()
        return settings.get("hooks", {})
    
    def get_output_level(self) -> str:
        """Get current hook output level."""
        settings = self._load_settings()
        return settings.get("hooks", {}).get("output_level", "all")

    def set_output_level(self, level: str) -> bool:
        """Set hook output level (silent, error, or all)."""
        if level not in ["silent", "error", "all"]:
            print(f"Error: Invalid output level '{level}'. Must be 'silent', 'error', or 'all'")
            return False

        # Create backup first
        self._create_backup()

        # Load current settings
        settings = self._load_settings()

        # Ensure hooks structure exists
        if "hooks" not in settings:
            settings["hooks"] = {}

        # Set output level
        settings["hooks"]["output_level"] = level

        # Save settings
        if self._save_settings(settings):
            print(f"Set hook output level to: {level}")
            return True
        else:
            print("Failed to save settings")
            return False

    def validate_settings(self) -> bool:
        """Validate the current settings file."""
        try:
            settings = self._load_settings()

            # Check basic structure
            if not isinstance(settings, dict):
                print("Error: Settings must be a JSON object")
                return False

            if "hooks" in settings:
                if not isinstance(settings["hooks"], dict):
                    print("Error: 'hooks' must be an object")
                    return False

                # Validate each hook event
                for event, matchers in settings["hooks"].items():
                    # Skip output_level as it's not an event
                    if event == "output_level":
                        continue

                    if not isinstance(matchers, list):
                        print(f"Error: Event '{event}' must contain a list")
                        return False

                    for matcher in matchers:
                        if not isinstance(matcher, dict):
                            print(f"Error: Matcher in '{event}' must be an object")
                            return False

                        if "hooks" in matcher:
                            if not isinstance(matcher["hooks"], list):
                                print(f"Error: 'hooks' in matcher must be a list")
                                return False

                            for hook in matcher["hooks"]:
                                if not isinstance(hook, dict):
                                    print(f"Error: Each hook must be an object")
                                    return False
                                if "type" not in hook or "command" not in hook:
                                    print(f"Error: Hook missing required fields (type, command)")
                                    return False

            print("Settings are valid")
            return True

        except Exception as e:
            print(f"Error validating settings: {e}")
            return False
    
    def restore_backup(self, backup_name: Optional[str] = None) -> bool:
        """Restore settings from a backup."""
        backups = sorted(self.backup_dir.glob("settings_*.json"))

        if not backups:
            print("No backups found")
            return False

        if backup_name:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                print(f"Backup not found: {backup_name}")
                return False
        else:
            # Use most recent backup
            backup_path = backups[-1]

        try:
            # Create backup of current state first
            self._create_backup()

            # Restore from backup
            shutil.copy2(backup_path, self.settings_path)
            print(f"Restored from: {backup_path.name}")
            return True

        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

    def show_installed_hooks(self) -> bool:
        """Show hooks that were selected during installation."""
        installed = self._load_installed_hooks()
        registry = self._load_hook_registry()

        if not installed:
            print("No installation record found (hooks-installed.json)")
            print("Run the hook installer to configure hooks:")
            print(f"  cd {self.hooks_dir}")
            print("  ./setup-hooks.sh")
            return False

        if not registry:
            print("Warning: Hook registry not found")
            registry = {"hooks": {}}

        installed_ids = installed.get("installed_hooks", [])
        hooks_metadata = installed.get("hooks", {})

        if not installed_ids:
            print("No hooks installed")
            return True

        print(f"Installed Hooks ({len(installed_ids)} total):")
        print()

        # Group by category
        by_category = {}
        for hook_id in installed_ids:
            hook_meta = hooks_metadata.get(hook_id, {})
            category = hook_meta.get("category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((hook_id, hook_meta))

        # Category names
        category_names = {
            "security": "Security & Safety",
            "quality": "Code Quality & Organization",
            "productivity": "Productivity & Notifications",
            "control": "Execution Control"
        }

        # Display by category
        for cat_id in ["security", "quality", "productivity", "control", "unknown"]:
            if cat_id not in by_category:
                continue

            cat_name = category_names.get(cat_id, cat_id.title())
            print(f"[{cat_name}]")

            for hook_id, hook_meta in by_category[cat_id]:
                name = hook_meta.get("name", hook_id)
                description = hook_meta.get("description", "")
                proj_marker = " [project-specific]" if hook_meta.get("project_specific") else ""

                # Get additional metadata from registry
                reg_info = registry.get("hooks", {}).get(hook_id, {})
                event = reg_info.get("event", "")
                matcher = reg_info.get("matcher", "")

                print(f"  • {name}{proj_marker}")
                if description:
                    print(f"    {description}")
                if event:
                    if matcher:
                        print(f"    Event: {event} | Matcher: {matcher}")
                    else:
                        print(f"    Event: {event}")

            print()

        print("To reconfigure hooks, run:")
        print(f"  cd {self.hooks_dir}")
        print("  ./setup-hooks.sh")

        return True

    def reconfigure_hooks(self, developer_mode: bool = False) -> bool:
        """Run the hook configuration script."""
        configure_script = self.hooks_dir / "setup-hooks.sh"

        if not configure_script.exists():
            print(f"Error: Configuration script not found: {configure_script}")
            return False

        print("Running hook configuration...")
        print()

        try:
            cmd = [str(configure_script)]
            if developer_mode:
                cmd.append("--developer")

            result = subprocess.run(cmd, cwd=self.hooks_dir)

            if result.returncode == 0:
                print()
                print("Hook reconfiguration complete")
                print("Important: Restart Claude Code for changes to take effect")
                return True
            else:
                print()
                print("Hook configuration was cancelled or failed")
                return False

        except Exception as e:
            print(f"Error running configuration: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Claude Code Hook Manager")
    parser.add_argument("--settings", "-s", 
                       help="Path to settings.json file",
                       default=os.path.expanduser("~/.claude/settings.json"))
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new hook")
    add_parser.add_argument("event", help="Hook event (PreToolUse, PostToolUse, etc.)")
    add_parser.add_argument("matcher", help="Tool matcher pattern")
    add_parser.add_argument("command", help="Command to execute")
    add_parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    add_parser.add_argument("--description", help="Hook description")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a hook")
    remove_parser.add_argument("event", help="Hook event")
    remove_parser.add_argument("matcher", help="Tool matcher pattern")
    remove_parser.add_argument("command", help="Command to remove")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all hooks")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate settings")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--backup", help="Specific backup to restore")

    # Output level commands
    output_parser = subparsers.add_parser("output", help="Get or set hook output level")
    output_parser.add_argument("level", nargs="?", choices=["silent", "error", "all"],
                              help="Set output level (omit to show current level)")

    # Installed hooks command
    installed_parser = subparsers.add_parser("installed", help="Show hooks selected during installation")

    # Reconfigure command
    reconfigure_parser = subparsers.add_parser("reconfigure", help="Run hook configuration again")
    reconfigure_parser.add_argument("--developer", action="store_true",
                                   help="Enable developer mode (all hooks)")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = HookManager(args.settings)
    
    if args.command == "add":
        success = manager.add_hook(
            args.event, 
            args.matcher, 
            args.command,
            args.timeout,
            args.description
        )
        return 0 if success else 1
    
    elif args.command == "remove":
        success = manager.remove_hook(args.event, args.matcher, args.command)
        return 0 if success else 1
    
    elif args.command == "list":
        hooks = manager.list_hooks()
        if hooks:
            print(json.dumps(hooks, indent=2))
        else:
            print("No hooks configured")
        return 0
    
    elif args.command == "validate":
        success = manager.validate_settings()
        return 0 if success else 1
    
    elif args.command == "restore":
        success = manager.restore_backup(args.backup)
        return 0 if success else 1

    elif args.command == "output":
        if args.level:
            # Set output level
            success = manager.set_output_level(args.level)
            return 0 if success else 1
        else:
            # Get current output level
            current = manager.get_output_level()
            print(f"Current hook output level: {current}")
            print("\nAvailable levels:")
            print("  silent - No output unless critical error")
            print("  error  - Only show output when hooks fail")
            print("  all    - Show all hook output (default)")
            return 0

    elif args.command == "installed":
        success = manager.show_installed_hooks()
        return 0 if success else 1

    elif args.command == "reconfigure":
        success = manager.reconfigure_hooks(args.developer)
        return 0 if success else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())