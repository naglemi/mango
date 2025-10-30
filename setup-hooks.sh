#!/bin/bash

# Setup Claude Code hooks with interactive configuration

# Base directory where this script lives
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Hooks directory
HOOKS_DIR="$BASE_DIR/hooks"

# Parse command line arguments
DEVELOPER_MODE=0
SHOW_HELP=0
UNINSTALL=0

for arg in "$@"; do
    case $arg in
        --developer)
            DEVELOPER_MODE=1
            shift
            ;;
        --help|-h)
            SHOW_HELP=1
            shift
            ;;
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        *)
            ;;
    esac
done

if [ $SHOW_HELP -eq 1 ]; then
    echo "Usage: ./setup-hooks.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --developer    Enable all hooks (developer mode)"
    echo "  --uninstall    Remove all hooks from Claude Code"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Default: Interactive hook selection with recommended defaults"
    exit 0
fi

# Uninstall mode
if [ $UNINSTALL -eq 1 ]; then
    echo "Uninstalling Claude Code hooks..."
    echo ""

    if [ ! -f ~/.claude/settings.json ]; then
        echo "No Claude Code settings found - nothing to uninstall"
        exit 0
    fi

    # Backup settings
    backup_file=~/.claude/settings.json.backup.$(date +%Y%m%d_%H%M%S)
    cp ~/.claude/settings.json "$backup_file"
    echo "Backed up settings to $backup_file"

    # Remove hooks section from settings
    python3 << 'EOF'
import json
import sys
from pathlib import Path

settings_file = Path.home() / ".claude" / "settings.json"

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)

    if "hooks" in settings:
        del settings["hooks"]

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        print("Removed all hooks from Claude settings")
    else:
        print("No hooks found in settings")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF

    # Remove installation record
    if [ -f "$HOOKS_DIR/hooks-installed.json" ]; then
        rm -f "$HOOKS_DIR/hooks-installed.json"
        echo "Removed installation record"
    fi

    echo ""
    echo "Uninstallation complete!"
    echo ""
    echo "Important: Restart Claude Code for changes to take effect"
    exit 0
fi

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code is not installed"
    echo "The 'claude' command was not found in PATH"
    exit 1
fi

echo "Setting up Claude Code Hooks..."
echo ""

# Check if Claude Code settings exist
if [ ! -f ~/.claude/settings.json ]; then
    echo "ERROR: Claude Code settings not found at ~/.claude/settings.json"
    echo "Please ensure Claude Code is installed and has been run at least once"
    exit 1
fi

# Configure hooks interactively
chmod +x "$HOOKS_DIR/configure-hooks.py"
chmod +x "$HOOKS_DIR/install-hooks.py"

if [ $DEVELOPER_MODE -eq 1 ]; then
    echo "Developer mode: Selecting all hooks"
    python3 "$HOOKS_DIR/configure-hooks.py" --developer
else
    echo "Interactive hook selection..."
    echo ""
    python3 "$HOOKS_DIR/configure-hooks.py"
fi

# Check if configuration was successful
if [ ! -f "$HOOKS_DIR/hooks-installed.json" ]; then
    echo ""
    echo "Hook configuration was cancelled or failed"
    echo "Run this script again to configure hooks"
    exit 0
fi

# Install hooks to Claude settings
echo ""
echo "Installing hooks to Claude Code..."
python3 "$HOOKS_DIR/install-hooks.py"

# Add 'hooks' alias to bashrc
echo ""
echo "Adding 'hooks' alias to ~/.bashrc..."

# Check if alias already exists
if grep -q "alias hooks=" ~/.bashrc 2>/dev/null; then
    echo "Alias already exists in ~/.bashrc"
else
    echo "" >> ~/.bashrc
    echo "# Added by mango/setup-hooks.sh" >> ~/.bashrc
    echo "alias hooks='python3 $HOOKS_DIR/configure-hooks.py'" >> ~/.bashrc
    echo "Added alias to ~/.bashrc"
    echo "Run: source ~/.bashrc"
    echo "Or restart your terminal for the 'hooks' command to work"
fi

echo ""
echo "Hook setup complete!"
echo ""
echo "To manage hooks later, run: hooks"
echo "To uninstall, run: ./setup-hooks.sh --uninstall"

