#!/bin/bash
# Tmux Auto-Launcher
# Prompts user on login to start tmux or resume existing sessions

# Only run if we're in an interactive shell and not already in tmux
if [[ $- != *i* ]] || [ -n "$TMUX" ]; then
    return 0 2>/dev/null || exit 0
fi

# Don't run in VS Code terminal, Claude Code, or other integrated terminals
# But DO run in regular macOS Terminal.app and iTerm
if [ -n "$VSCODE_INJECTION" ]; then
    return 0 2>/dev/null || exit 0
fi

# Skip for specific integrated terminals, but allow macOS Terminal.app and iTerm2
case "$TERM_PROGRAM" in
    "vscode"|"Claude"|"kiro")
        return 0 2>/dev/null || exit 0
        ;;
esac

# Get the directory where this script lives
# Use ${BASH_SOURCE[0]} for bash, ${(%):-%x} for zsh
if [ -n "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "$ZSH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
else
    echo "ERROR: Cannot determine script directory - unknown shell"
    return 1 2>/dev/null || exit 1
fi

# Launch the session menu with Desktop/Mobile presets
if [ ! -f "$SCRIPT_DIR/tmux-session-menu.sh" ]; then
    echo "ERROR: tmux-session-menu.sh not found at $SCRIPT_DIR"
    return 1 2>/dev/null || exit 1
fi

source "$SCRIPT_DIR/tmux-session-menu.sh"
