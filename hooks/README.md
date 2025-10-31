# Claude Code Hook Management System

A comprehensive system for managing Claude Code hooks with 30+ security and workflow enforcement hooks, an interactive control panel, and tmux integration.

## What It Does

The hook system provides:

- **30+ Security & Workflow Hooks** - Enforce coding standards, block dangerous operations, and guide better practices
- **Interactive TUI Control Panel** - Enable/disable/configure hooks with a checkbox interface
- **Tmux Integration** - Access hook controls with `Ctrl+b k` 
- **Command Line Tools** - Install, manage, and configure hooks from anywhere
- **Safe Settings Management** - Atomic operations with automatic backups
- **Flexible Scopes** - Global, project, or local hook configurations

## Quick Start

### Complete Installation

```bash
# 1. Install the hook system
cd /path/to/usability/hooks
./install.sh

# 2. Set up tmux integration (optional but recommended)
cd ../tmux
./setup-tmux.sh

# 3. Make 'hooks' command available globally
cd ../hooks
sudo ./setup-hooks-command.sh

# 4. Restart tmux and Claude Code
```

### Access Hook Control Panel

**Method 1: From tmux** (recommended)
- Press `Ctrl+b k` to launch the interactive hook selector

**Method 2: From command line**
```bash
hooks          # Launch interactive control panel
# or
python3 /path/to/usability/hooks/hook_selector.py
```

**Method 3: From Claude Code**
- Type `/hooks` in any Claude conversation

## Available Hook Categories

### Security Hooks
- `protect-env-vars` - Blocks exposure of sensitive environment variables
- `block-rm` - Prevents dangerous file deletion commands
- `block-git-stash` - Blocks potentially lossy git stash operations
- `block-commit-to-main` - Prevents direct commits to main branch

### Code Quality Hooks  
- `auto-lint-python` - Automatically lint Python files before operations
- `python-lint-before-run` - Require linting before running Python scripts
- `block-bad-filenames` - Enforce good filename conventions
- `block-error-hiding` - Prevent suppression of important errors

### Workflow Enforcement Hooks
- `block-search-tools` - Block Glob/Grep tools to encourage reading full files
- `block-head-tail` - Prevent partial file reading, encourage full file reads
- `limit-line-count` - Soft limit on file line counts with warnings
- `strict-limit-line-count` - Hard limit on file line counts
- `block-md-files` - Prevent creation of unnecessary documentation files

### Safety Hooks
- `block-sed-editing` - Prevent risky sed-based file editing
- `force-background-bash` - Force long-running commands to background
- `block-scripts-dirty-git` - Prevent script creation with uncommitted changes

## Hook Control Panel Features

The interactive TUI (`Ctrl+b k`) provides:

- **[Space]** - Toggle hooks on/off
- **[C]** - Configure environment variables for hooks
- **[M]** - Customize messages shown when hooks trigger  
- **[D]** - View detailed hook information
- **[I]** - Launch Claude conversation in hooks directory
- **[K]** - Kill zombie hook processes
- **[Q]** - Quit

## Command Line Usage

### List Available Hooks
```bash
python3 hooks/hook_installer.py list
python3 hooks/hook_installer.py list --category security
```

### Install Hooks
```bash
# Install single hook to project
python3 hooks/hook_installer.py install protect-env-vars

# Install to global settings (affects all projects)
python3 hooks/hook_installer.py install protect-env-vars --scope global

# Install entire category
python3 hooks/hook_installer.py install-category security
```

### Manage Settings Directly
```bash
# List currently configured hooks
python3 hooks/hook_manager.py list

# Add custom hook
python3 hooks/hook_manager.py add PreToolUse "Bash" "/path/to/script.py"

# Remove hook
python3 hooks/hook_manager.py remove PreToolUse "Bash" "/path/to/script.py"

# Validate settings file
python3 hooks/hook_manager.py validate

# Restore from backup
python3 hooks/hook_manager.py restore
```

## Installation Details

The system requires these components:

1. **Core Scripts**: `hook_manager.py`, `hook_installer.py`, `hook_selector.py`
2. **Registry Files**: `hook_registry.json`, `hook_messages.json` 
3. **Hook Scripts**: 30+ individual `.py` hook scripts
4. **Shell Integration**: `setup-hooks-command.sh` for global `hooks` command
5. **Tmux Integration**: `tmux.conf` with `Ctrl+b k` binding

## Troubleshooting

### Hook Control Panel Won't Launch
```bash
# Check if hooks command is available
which hooks

# If not, run setup again
sudo /path/to/usability/hooks/setup-hooks-command.sh

# Or run directly
python3 /path/to/usability/hooks/hook_selector.py
```

### Hooks Not Triggering
```bash
# Validate settings
python3 hooks/hook_manager.py validate

# Check if hooks are registered  
python3 hooks/hook_manager.py list

# Run Claude with debug
claude --debug
```

### Settings File Corrupted
```bash
# Restore from automatic backup
python3 hooks/hook_manager.py restore

# Validate current settings
python3 hooks/hook_manager.py validate
```

### Permission Issues
```bash
# Make scripts executable
chmod +x hooks/*.py hooks/*.sh
```

## Hook Scopes

- **Global** (`~/.claude/settings.json`) - Affects all Claude projects
- **Project** (`.claude/settings.json`) - Project-specific, committed to git
- **Local** (`.claude/settings.local.json`) - Project-specific, not committed

## Key Features

### Safe Settings Management
- Atomic file operations (write to temp, then replace)
- Automatic backups before changes
- File locking prevents concurrent modifications
- JSON validation before saving

### Flexible Configuration
- Environment variable configuration for hooks
- Custom messages for hook triggers
- Category-based bulk operations
- Dependency checking

### Tmux Integration  
- `Ctrl+b k` - Launch hook control panel
- `Ctrl+Shift+A` - Copy entire scrollback to clipboard
- Seamless integration with existing tmux workflows

## Documentation

- `HOOK_MANAGEMENT.md` - Detailed system documentation
- `HOOKS_REFERENCE.txt` - Complete hook reference
- Individual hook files contain inline documentation

## Philosophy

The system enforces the philosophy: **read entire files, navigate intelligently**. It blocks tools that encourage partial reading and guides users toward better development practices through enforced workflows.