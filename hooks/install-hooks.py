#!/usr/bin/env python3
"""
Install selected hooks to Claude Code settings
Reads hooks-installed.json and configures ~/.claude/settings.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_hook_registry(hooks_dir):
    """Load the hook registry with hook metadata"""
    registry_file = Path(hooks_dir) / "hook_registry.json"
    with open(registry_file, 'r') as f:
        return json.load(f)

def load_installed_hooks(hooks_dir):
    """Load the list of hooks user selected"""
    installed_file = Path(hooks_dir) / "hooks-installed.json"
    if not installed_file.exists():
        print(f"ERROR: {installed_file} not found")
        print("Run configure-hooks.py first to select hooks")
        sys.exit(1)

    with open(installed_file, 'r') as f:
        return json.load(f)

def load_claude_settings():
    """Load current Claude Code settings"""
    settings_file = Path.home() / ".claude" / "settings.json"

    if not settings_file.exists():
        print(f"ERROR: {settings_file} not found")
        print("Claude Code settings file doesn't exist")
        sys.exit(1)

    with open(settings_file, 'r') as f:
        return json.load(f)

def save_claude_settings(settings):
    """Save updated Claude Code settings"""
    settings_file = Path.home() / ".claude" / "settings.json"

    # Backup current settings
    backup_file = settings_file.parent / f"settings.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if settings_file.exists():
        import shutil
        shutil.copy(settings_file, backup_file)
        print(f"Backed up existing settings to {backup_file}")

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)

    return settings_file

def build_hook_configuration(installed_hooks, registry, hooks_dir):
    """Build Claude Code hook configuration from selected hooks"""

    # Get list of installed hook IDs
    installed_ids = set(installed_hooks["installed_hooks"])

    # Build hooks by event and matcher
    hooks_by_event = {}

    for hook_id in installed_ids:
        if hook_id not in registry["hooks"]:
            print(f"Warning: Hook '{hook_id}' not found in registry, skipping")
            continue

        hook_info = registry["hooks"][hook_id]
        script = hook_info["script"]
        event = hook_info["event"]
        matcher = hook_info.get("matcher", "")
        timeout = hook_info.get("timeout", 5)

        # Build hook entry - handle both .py and .sh scripts
        if script.endswith('.py'):
            command = f"python3 {hooks_dir}/{script}"
        else:
            command = f"{hooks_dir}/{script}"

        hook_entry = {
            "type": "command",
            "command": command
        }

        if timeout:
            hook_entry["timeout"] = timeout

        # Organize by event and matcher
        if event not in hooks_by_event:
            hooks_by_event[event] = {}

        if matcher not in hooks_by_event[event]:
            hooks_by_event[event][matcher] = []

        hooks_by_event[event][matcher].append(hook_entry)

    # Convert to Claude Code settings format
    settings_hooks = {}

    for event, matchers in hooks_by_event.items():
        if event not in settings_hooks:
            settings_hooks[event] = []

        for matcher, hooks in matchers.items():
            # All hooks use matcher/hooks format (even with empty matcher for Stop events)
            settings_hooks[event].append({
                "matcher": matcher,
                "hooks": hooks
            })

    return settings_hooks

def main():
    print("Installing selected hooks to Claude Code...")
    print()

    # Get hooks directory
    hooks_dir = Path(__file__).parent

    # Load configurations
    try:
        registry = load_hook_registry(hooks_dir)
        installed = load_installed_hooks(hooks_dir)
        settings = load_claude_settings()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Build hook configuration
    hooks_config = build_hook_configuration(installed, registry, hooks_dir)

    # Update settings
    settings["hooks"] = hooks_config

    # Set default custom settings if not present
    if "alwaysThinkingEnabled" not in settings:
        settings["alwaysThinkingEnabled"] = True

    if "custom_status_line_enabled" not in settings:
        settings["custom_status_line_enabled"] = True

    if "skip_close_pane_confirmation" not in settings:
        settings["skip_close_pane_confirmation"] = True

    if "tmux_color_notifications_enabled" not in settings:
        settings["tmux_color_notifications_enabled"] = True

    if "tmux_idle_color" not in settings:
        settings["tmux_idle_color"] = "blue"

    if "tmux_active_color" not in settings:
        settings["tmux_active_color"] = "default"

    if "statusLine" not in settings:
        statusline_script = Path.home() / ".claude" / "statusline.sh"
        if statusline_script.exists():
            settings["statusLine"] = {
                "type": "command",
                "command": str(statusline_script),
                "padding": 0,
                "updateIntervalSeconds": 30
            }

    # Save settings
    settings_file = save_claude_settings(settings)

    print(f"Installed {len(installed['installed_hooks'])} hooks to {settings_file}")
    print()
    print("Hooks installed by event:")
    for event in hooks_config:
        if isinstance(hooks_config[event], list):
            if event in ["PreToolUse"]:
                # Count hooks across all matchers
                total = sum(len(m.get("hooks", [])) for m in hooks_config[event])
                print(f"  {event}: {total} hooks")
            else:
                print(f"  {event}: {len(hooks_config[event])} hooks")
        else:
            print(f"  {event}: direct hooks")

    print()
    print("Important: Restart Claude Code for changes to take effect")

    return 0

if __name__ == "__main__":
    sys.exit(main())
