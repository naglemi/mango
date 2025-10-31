#!/usr/bin/env bash
# Battlestation Preset: One window with four panes
# Top-left: nvim, Bottom-left: lazygit, Top-right: claude, Bottom-right: hook manager

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│       BATTLESTATION PRESET           │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ One window, four panes:                ${CYAN}│${NC}"
echo -e "${CYAN}│                                         ${CYAN}│${NC}"
echo -e "${CYAN}│  ┌──────────────┬──────────────┐        ${CYAN}│${NC}"
echo -e "${CYAN}│  │ ${GREEN}nvim${NC}         │ ${GREEN}claude${NC}       │        ${CYAN}│${NC}"
echo -e "${CYAN}│  ├──────────────┼──────────────┤        ${CYAN}│${NC}"
echo -e "${CYAN}│  │ ${GREEN}lazygit${NC}      │ ${GREEN}hooks${NC}        │        ${CYAN}│${NC}"
echo -e "${CYAN}│  └──────────────┴──────────────┘        ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[C]${NC} Continue with setup               ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Cancel                            ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Get user choice
read -n1 -p "Continue? [C/Q]: " choice
echo
echo

if [[ ! $choice =~ ^[Cc]$ ]]; then
    echo -e "${BLUE} Cancelled${NC}"
    exit 0
fi

# Claude Code options submenu
get_claude_options() {
    echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}" >&2
    echo -e "${CYAN}│          CLAUDE CODE OPTIONS         │${NC}" >&2
    echo -e "${CYAN}├─────────────────────────────────────────┤${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[1]${NC} New (safe)                        ${CYAN}│${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[2]${NC} New (skip permissions)            ${CYAN}│${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[3]${NC} Continue (safe)                   ${CYAN}│${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[4]${NC} Continue (skip permissions)       ${CYAN}│${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[5]${NC} Resume (safe)                     ${CYAN}│${NC}" >&2
    echo -e "${CYAN}│  ${GREEN}[6]${NC} Resume (skip permissions)         ${CYAN}│${NC}" >&2
    echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}" >&2
    echo >&2

    read -n1 -p "Select Claude option: " claude_choice
    echo >&2
    echo >&2

    case "$claude_choice" in
        1) echo "claude" ;;
        2) echo "claude --dangerously-skip-permissions" ;;
        3) echo "claude --continue" ;;
        4) echo "claude --continue --dangerously-skip-permissions" ;;
        5) echo "claude --resume" ;;
        6) echo "claude --resume --dangerously-skip-permissions" ;;
        *)
            echo -e "${RED} Invalid option, using default (new, safe)${NC}" >&2
            echo "claude"
            ;;
    esac
}

# Get Claude command
CLAUDE_CMD=$(get_claude_options)

# Check for lazygit
if ! command -v lazygit &> /dev/null; then
    echo -e "${YELLOW}  lazygit not found, using git status instead${NC}"
    LAZYGIT_CMD="bash -c 'git status; echo; echo Press Ctrl+C to exit; read'"
else
    LAZYGIT_CMD="lazygit"
fi

# Get project directory
echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│       PROJECT DIRECTORY              │${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo
echo -e "${CYAN}Enter project directory (or Enter for current directory):${NC}"
echo -e "${BLUE}Current: $(pwd)${NC}"
read -r PROJECT_DIR

# Use current directory if empty
if [ -z "$PROJECT_DIR" ]; then
    WORK_DIR="$(pwd)"
    echo -e "${GREEN} Using current directory: $WORK_DIR${NC}"
else
    # Expand ~ to home directory
    PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"

    # Check if directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${YELLOW}  Directory does not exist: $PROJECT_DIR${NC}"
        echo -e "${CYAN}Create it? [y/N]:${NC}"
        read -n1 -r create_dir
        echo

        if [[ $create_dir =~ ^[Yy]$ ]]; then
            mkdir -p "$PROJECT_DIR"
            echo -e "${GREEN} Created directory: $PROJECT_DIR${NC}"
            WORK_DIR="$PROJECT_DIR"
        else
            echo -e "${RED} Cancelled - directory does not exist${NC}"
            exit 1
        fi
    else
        WORK_DIR="$PROJECT_DIR"
        echo -e "${GREEN} Using project directory: $WORK_DIR${NC}"
    fi
fi
echo

echo -e "${GREEN} Creating Battlestation layout...${NC}"

# Ask for session name if not in tmux
if [ -z "$TMUX" ]; then
    echo -e "${CYAN}Session name (or Enter for auto-generated):${NC}"
    read -r SESSION_NAME
    if [ -z "$SESSION_NAME" ]; then
        SESSION_NAME="battlestation-${USER}-$$"
    fi
    echo
fi

# Create session if not in tmux
if [ -z "$TMUX" ]; then
    tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR"
    TMUX_TARGET="$SESSION_NAME"
else
    # If in tmux, we'll create a window in current session
    TMUX_TARGET=""
fi

# Create the four-pane layout
# Start with nvim in the first pane
tmux send-keys -t "$TMUX_TARGET" "nvim" C-m

# Split vertically to create right column (nvim left, new pane right)
tmux split-window -t "$TMUX_TARGET" -h -c "$WORK_DIR" "$CLAUDE_CMD"

# Select left pane and split horizontally (nvim top-left, new pane bottom-left)
tmux select-pane -t "$TMUX_TARGET:1.0"
tmux split-window -t "$TMUX_TARGET" -v -c "$WORK_DIR" "$LAZYGIT_CMD"

# Select right pane and split horizontally (claude top-right, new pane bottom-right)
tmux select-pane -t "$TMUX_TARGET:1.2"
tmux split-window -t "$TMUX_TARGET" -v -c "$WORK_DIR"

# In the bottom-right pane, start a hook manager interface
HOOK_SCRIPT="$WORK_DIR/.claude/hooks"
if [ -d "$HOOK_SCRIPT" ]; then
    HOOK_DIR="$HOOK_SCRIPT"
else
    HOOK_DIR="$HOME/.config/claude/hooks"
fi

# Create a simple hook manager command
HOOK_MANAGER_CMD="bash -c 'echo \"═══════════════════════════════════════\"; echo \"    CLAUDE HOOKS MANAGER\"; echo \"═══════════════════════════════════════\"; echo; echo \"Hook directory: $HOOK_DIR\"; echo; if [ -d \"$HOOK_DIR\" ]; then echo \"Available hooks:\"; ls -1 \"$HOOK_DIR\" 2>/dev/null || echo \"  (no hooks found)\"; else echo \"  Hook directory not found\"; fi; echo; echo \"Commands:\"; echo \"  - Press ENTER to list hooks\"; echo \"  - Type hook name to view/edit\"; echo \"  - Ctrl+C to exit\"; echo; while true; do read -p \"Hook > \" hook; if [ -f \"$HOOK_DIR/\$hook\" ]; then \$EDITOR \"$HOOK_DIR/\$hook\" || cat \"$HOOK_DIR/\$hook\"; else echo \"Hook not found: \$hook\"; fi; echo; ls -1 \"$HOOK_DIR\" 2>/dev/null; echo; done'"

tmux send-keys -t "$TMUX_TARGET:1.3" "$HOOK_MANAGER_CMD" C-m

# Select the top-left pane (nvim) to start
tmux select-pane -t "$TMUX_TARGET:1.0"

# Attach if we created a new session
if [ -z "$TMUX" ]; then
    tmux attach -t "$SESSION_NAME"
fi

echo -e "${GREEN} Battlestation preset created!${NC}"
echo -e ""
echo -e "  Layout:"
echo -e "  ┌──────────────┬──────────────┐"
echo -e "  │ nvim         │ claude       │"
echo -e "  ├──────────────┼──────────────┤"
echo -e "  │ lazygit      │ hooks        │"
echo -e "  └──────────────┴──────────────┘"
echo -e ""
echo -e "  ${CYAN}Ctrl+B arrow keys${NC} - Navigate between panes"
echo -e "  ${CYAN}Ctrl+B o${NC}          - Cycle through panes"
echo -e "  ${CYAN}Ctrl+B z${NC}          - Zoom/unzoom current pane"
