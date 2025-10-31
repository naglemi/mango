#!/usr/bin/env bash
# Mobile Preset: Three separate windows with enlarged status bar

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│          MOBILE PRESET               │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ Window 1: ${GREEN}nvim${NC}                         ${CYAN}│${NC}"
echo -e "${CYAN}│ Window 2: ${GREEN}claude${NC}                       ${CYAN}│${NC}"
echo -e "${CYAN}│ Window 3: ${GREEN}lazygit${NC}                      ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ Enlarged status bar for easier tapping ${CYAN}│${NC}"
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

echo -e "${GREEN} Creating Mobile layout...${NC}"

# Ask for session name if not in tmux
if [ -z "$TMUX" ]; then
    echo -e "${CYAN}Session name (or Enter for auto-generated):${NC}"
    read -r SESSION_NAME
    if [ -z "$SESSION_NAME" ]; then
        SESSION_NAME="mobile-${USER}-$$"
    fi
    echo
fi

# Create session if not in tmux
if [ -z "$TMUX" ]; then
    tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR"
    TMUX_TARGET="$SESSION_NAME"
else
    # If in tmux, we'll create windows in current session
    TMUX_TARGET=""
fi

# Configure mobile-friendly status bar (larger, more visible) - grayscale with LIST/ICONS buttons
tmux set-option -t "$TMUX_TARGET" status-style "bg=#2a2a2a,fg=#d0d0d0"
tmux set-option -t "$TMUX_TARGET" status-left-length 40
tmux set-option -t "$TMUX_TARGET" status-right-length 60
tmux set-option -t "$TMUX_TARGET" window-status-separator ''
tmux set-option -t "$TMUX_TARGET" window-status-style "bg=#3a3a3a,fg=#d0d0d0"
tmux set-option -t "$TMUX_TARGET" window-status-current-style "bg=#5a5a5a,fg=#ffffff,bold"
tmux set-option -t "$TMUX_TARGET" window-status-format " #I:#W "
tmux set-option -t "$TMUX_TARGET" window-status-current-format " #I:#W "
tmux set-option -t "$TMUX_TARGET" status-left "#[bg=#4a4a4a,fg=#ffffff,bold] L I S T  "
tmux set-option -t "$TMUX_TARGET" status-right "#[bg=#4a4a4a,fg=#ffffff,bold] I C O N S 🥭 "

# Window 1: nvim
tmux send-keys -t "$TMUX_TARGET" "nvim" C-m
tmux rename-window -t "$TMUX_TARGET:1" "nvim"

# Window 2: claude
tmux new-window -t "$TMUX_TARGET" -c "$WORK_DIR" -n "claude" "$CLAUDE_CMD"

# Window 3: lazygit
tmux new-window -t "$TMUX_TARGET" -c "$WORK_DIR" -n "git" "$LAZYGIT_CMD"

# Switch back to window 1
tmux select-window -t "$TMUX_TARGET:1"

# Attach if we created a new session
if [ -z "$TMUX" ]; then
    tmux attach -t "$SESSION_NAME"
fi

echo -e "${GREEN} Mobile preset created!${NC}"
echo -e "  Window 1: nvim"
echo -e "  Window 2: claude"
echo -e "  Window 3: git"
echo -e ""
echo -e "  ${CYAN}Ctrl+B 1${NC} - nvim window"
echo -e "  ${CYAN}Ctrl+B 2${NC} - claude window"
echo -e "  ${CYAN}Ctrl+B 3${NC} - git window"
echo -e ""
echo -e "  ${YELLOW}Enlarged status bar for mobile-friendly tapping${NC}"
