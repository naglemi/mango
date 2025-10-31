#!/bin/bash
# Robust tmux session manager with preset support

# Get the directory where this script lives
if [ -n "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "$ZSH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
else
    echo "ERROR: Cannot determine script directory - unknown shell"
    return 1 2>/dev/null || exit 1
fi

# Check if we're in an interactive terminal context
if [ -z "$TERM" ]; then
    if ! stty -g &>/dev/null 2>&1; then
        return 0 2>/dev/null || exit 0
    fi
fi

# Exit if already in tmux
if [ -n "$TMUX" ]; then
    return 0 2>/dev/null || exit 0
fi

# Check if tmux command exists
if ! command -v tmux &> /dev/null; then
    return 0 2>/dev/null || exit 0
fi

# Get existing sessions
session_list=$(tmux list-sessions -F '#S' 2>/dev/null || true)

if [ -z "$session_list" ]; then
    has_sessions=0
else
    has_sessions=1
fi

# Print header
echo ""
echo "═══════════════════════════════════════════"
if [ "$has_sessions" = "1" ]; then
    echo "           TMUX SESSIONS AVAILABLE"
else
    echo "             TMUX MENU"
fi
echo "═══════════════════════════════════════════"

# Require fzf - no fallback
if ! command -v fzf &>/dev/null; then
    echo "   ERROR: fzf is required but not installed"
    echo "  Install: brew install fzf (macOS) or apt install fzf (Linux)"
    echo ""
    echo "═══════════════════════════════════════════"
    return 1 2>/dev/null || exit 1
fi

echo "  Use arrows/type to filter, Space to select, Enter to confirm"
echo "───────────────────────────────────────────"

# Build options - existing sessions first, then presets, then settings/uninstall
if [ "$has_sessions" = "1" ]; then
    all_options=$(echo -e "$session_list\n───────────────────────────\n[New Session]\n  Desktop Preset (2 windows)\n Mobile Preset (3 windows)\n Battlestation Preset (4 panes)\n───────────────────────────\n[Settings]\n[Uninstall Auto-Launcher]\n[Skip]")
else
    all_options=$(echo -e "[New Session]\n  Desktop Preset (2 windows)\n Mobile Preset (3 windows)\n Battlestation Preset (4 panes)\n───────────────────────────\n[Settings]\n[Uninstall Auto-Launcher]\n[Skip]")
fi

choice=$(echo "$all_options" | fzf --height=20 --reverse --prompt="  Select> " --no-info --ansi)

case "$choice" in
    "  Desktop Preset (2 windows)")
        echo "   Launching Desktop preset..."
        "$SCRIPT_DIR/preset-desktop.sh"
        return 0 2>/dev/null || exit 0
        ;;
    " Mobile Preset (3 windows)")
        echo "   Launching Mobile preset..."
        "$SCRIPT_DIR/preset-mobile.sh"
        return 0 2>/dev/null || exit 0
        ;;
    " Battlestation Preset (4 panes)")
        echo "   Launching Battlestation preset..."
        "$SCRIPT_DIR/preset-battlestation.sh"
        return 0 2>/dev/null || exit 0
        ;;
    "[New Session]")
        echo "   Creating new tmux session"
        echo -n "  Session name (or Enter for default): "
        read -r session_name
        if [ -n "$session_name" ]; then
            exec tmux new -s "$session_name"
        else
            exec tmux new
        fi
        ;;
    "[Settings]")
        echo "   Launching Settings panel..."
        python3 "$SCRIPT_DIR/settings-menu.py"
        return 0 2>/dev/null || exit 0
        ;;
    "[Uninstall Auto-Launcher]")
        echo "  Uninstalling tmux auto-launcher..."
        if [ -f ~/.zshrc ]; then
            grep -v "tmux-auto-launcher.sh" ~/.zshrc > ~/.zshrc.tmp && mv ~/.zshrc.tmp ~/.zshrc
            echo "   Removed from ~/.zshrc"
        elif [ -f ~/.bashrc ]; then
            grep -v "tmux-auto-launcher.sh" ~/.bashrc > ~/.bashrc.tmp && mv ~/.bashrc.tmp ~/.bashrc
            echo "   Removed from ~/.bashrc"
        fi
        echo "  ℹ  Manual uninstall: Remove lines containing 'tmux-auto-launcher.sh' from your shell config"
        ;;
    "[Skip]"|""|"───────────────────────────")
        echo "   Continuing without tmux"
        ;;
    *)
        if [ -n "$choice" ]; then
            echo "   Attaching to session: $choice"
            tmux attach -t "$choice"
        fi
        ;;
esac

echo "═══════════════════════════════════════════"
echo ""
