# Claude Code Hook Management System

A comprehensive system for safely managing Claude Code hooks without corrupting settings.json files.

## Overview

This system provides three main components:

1. **Hook Manager** (`hook_manager.py`) - Safely manipulates settings.json files
2. **Hook Registry** (`hook_registry.json`) - Catalog of available hooks
3. **Hook Installer** (`hook_installer.py`) - Installs hooks from registry

## Features

### Safe JSON Manipulation
- Atomic file operations (write to temp, then replace)
- File locking to prevent concurrent modifications
- Automatic backups before changes
- JSON validation before saving
- Preserves formatting and structure

### Hook Registry System
- Centralized catalog of available hooks
- Categorization (security, quality, safety, productivity)
- Dependency tracking
- Compatibility information (global vs project)
- Metadata (author, tags, description)

### Installation Management
- Install to global, project, or local settings
- Automatic dependency checking
- Category-based bulk installation
- Script copying for project-specific installations

## Quick Start

### 1. List Available Hooks

```bash
# List all available hooks
python3 hooks/hook_installer.py list

# List hooks by category
python3 hooks/hook_installer.py list --category security
```

### 2. Install a Hook

```bash
# Install to project settings (default)
python3 hooks/hook_installer.py install protect-env-vars

# Install globally (affects all projects)
python3 hooks/hook_installer.py install protect-env-vars --scope global

# Install to local settings (not committed to git)
python3 hooks/hook_installer.py install protect-env-vars --scope local
```

### 3. Install a Category

```bash
# Install all security hooks to project
python3 hooks/hook_installer.py install-category security

# Install all quality hooks globally
python3 hooks/hook_installer.py install-category quality --scope global
```

### 4. Manage Hooks Directly

```bash
# Add a custom hook
python3 hooks/hook_manager.py add PreToolUse "Bash" "/path/to/script.py" --timeout 10

# Remove a hook
python3 hooks/hook_manager.py remove PreToolUse "Bash" "/path/to/script.py"

# List configured hooks
python3 hooks/hook_manager.py list

# Validate settings file
python3 hooks/hook_manager.py validate

# Restore from backup
python3 hooks/hook_manager.py restore
```

## Hook Scopes

### Global Hooks (`~/.claude/settings.json`)
- Affect all Claude Code sessions
- Good for security policies, universal standards
- Scripts use absolute paths

### Project Hooks (`.claude/settings.json`)
- Specific to a project/repository
- Committed to version control
- Scripts use `$CLAUDE_PROJECT_DIR` variable

### Local Hooks (`.claude/settings.local.json`)
- Project-specific but not committed
- Personal preferences or local environment
- Overrides project settings

## Creating Custom Hooks

### 1. Create Hook Script

```bash
# Create from template
python3 hooks/hook_installer.py create my-custom-hook --template validator
```

### 2. Edit the Script

```python
#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Your validation logic here
    if some_condition:
        print("Error message", file=sys.stderr)
        sys.exit(2)  # Block operation
    
    sys.exit(0)  # Allow operation
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

### 3. Register in Registry

Add to `hook_registry.json`:

```json
{
  "my-custom-hook": {
    "name": "My Custom Hook",
    "description": "Description of what it does",
    "script": "my-custom-hook.py",
    "event": "PreToolUse",
    "matcher": "Bash",
    "timeout": 5,
    "tags": ["custom"],
    "compatible_with": ["global", "project"]
  }
}
```

### 4. Install

```bash
python3 hooks/hook_installer.py install my-custom-hook
```

## Examples

### Example 1: Protect Critical Files

```python
#!/usr/bin/env python3
# protect-critical-files.py
import json
import sys

PROTECTED_FILES = [
    "production.env",
    "credentials.json",
    ".env.production"
]

try:
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        
        for protected in PROTECTED_FILES:
            if protected in file_path:
                print(f"Cannot modify protected file: {protected}", file=sys.stderr)
                sys.exit(2)
    
    sys.exit(0)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

### Example 2: Enforce Branch Protection

```python
#!/usr/bin/env python3
# enforce-branch-protection.py
import json
import sys
import subprocess

def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

try:
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Check for git push to protected branches
        if "git push" in command:
            current_branch = get_current_branch()
            if current_branch in ["main", "master", "production"]:
                print(f"Direct push to {current_branch} is not allowed", file=sys.stderr)
                print("Please create a feature branch and pull request", file=sys.stderr)
                sys.exit(2)
    
    sys.exit(0)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

## Backup and Recovery

The hook manager automatically creates backups before any changes:

```bash
# Backups are stored in .claude_backups/
ls .claude/.claude_backups/

# Restore latest backup
python3 hooks/hook_manager.py restore

# Restore specific backup
python3 hooks/hook_manager.py restore --backup settings_20240101_120000.json
```

## Best Practices

1. **Test hooks locally first** - Use `--scope local` for testing
2. **Use categories** - Install related hooks together
3. **Check dependencies** - Ensure required tools are installed
4. **Keep backups** - System auto-backs up, but manual backups are good too
5. **Validate regularly** - Run `validate` command after manual edits
6. **Use appropriate scope** - Global for policies, project for team standards
7. **Document custom hooks** - Add clear descriptions and examples

## Troubleshooting

### Settings file corrupted
```bash
# Validate and show errors
python3 hooks/hook_manager.py validate

# Restore from backup
python3 hooks/hook_manager.py restore
```

### Hook not triggering
1. Check if hook is registered: `python3 hooks/hook_manager.py list`
2. Verify matcher pattern matches tool name
3. Check script permissions (must be executable)
4. Use `claude --debug` to see hook execution

### Permission denied
```bash
# Make scripts executable
chmod +x hooks/*.py hooks/*.sh
```

### Dependencies missing
```bash
# Check what's missing
python3 hooks/hook_installer.py install <hook-id>
# Install missing dependencies manually
```

## Security Considerations

1. **Review hook scripts** - Understand what they do before installing
2. **Use appropriate scope** - Don't install untrusted hooks globally
3. **Check file paths** - Hooks using absolute paths have system access
4. **Validate inputs** - Hooks should sanitize all inputs
5. **Test in isolation** - Use project/local scope for testing

## Integration with CI/CD

```yaml
# .github/workflows/validate-hooks.yml
name: Validate Hooks
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate settings
        run: |
          python3 hooks/hook_manager.py validate --settings .claude/settings.json
      - name: Test hooks
        run: |
          python3 hooks/test_protect_env_vars.py
```

## Advanced Usage

### Programmatic Hook Management

```python
from hook_manager import HookManager

# Initialize manager
manager = HookManager(".claude/settings.json")

# Add hook programmatically
manager.add_hook(
    event="PreToolUse",
    matcher="Bash",
    command="/path/to/script.py",
    timeout=10,
    description="My custom hook"
)

# List all hooks
hooks = manager.list_hooks()
print(json.dumps(hooks, indent=2))

# Validate settings
if manager.validate_settings():
    print("Settings are valid")
```

### Bulk Operations

```python
from hook_installer import HookInstaller

installer = HookInstaller()

# Install multiple hooks
hooks_to_install = ["protect-env-vars", "check-secrets", "backup-before-edit"]
for hook_id in hooks_to_install:
    installer.install_hook(hook_id, scope="project")

# Install all security hooks globally
installer.install_category("security", scope="global")
```

## Summary

This hook management system provides:
- **Safety**: Atomic operations, backups, validation
- **Flexibility**: Multiple scopes, categories, custom hooks
- **Ease of use**: Simple CLI commands, templates
- **Robustness**: Error handling, dependency checking
- **Integration**: CI/CD ready, programmatic API

Use this system to safely manage Claude Code hooks across your projects without fear of corrupting settings files.