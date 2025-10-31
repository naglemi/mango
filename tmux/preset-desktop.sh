#!/usr/bin/env bash
# Desktop Preset: Two windows - (nvim+claude split) and lazygit

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│           DESKTOP PRESET             │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│ Claude always on RIGHT in Window 1    ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[1]${NC} W1: nvim+claude  W2: lazygit     ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[2]${NC} W1: lazygit+claude  W2: nvim     ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Cancel                            ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Get user choice
read -n1 -p "Select layout: " choice
echo
echo

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

# Ask for session name if not in tmux
if [ -z "$TMUX" ]; then
    echo -e "${CYAN}Session name (or Enter for auto-generated):${NC}"
    read -r SESSION_NAME
    if [ -z "$SESSION_NAME" ]; then
        SESSION_NAME="desktop-${USER}-$$"
    fi
    echo
fi

case "$choice" in
    1)
        echo -e "${GREEN}  Creating Desktop layout (nvim left, claude right)...${NC}"

        # Create session if not in tmux
        if [ -z "$TMUX" ]; then
            tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR"
            TMUX_TARGET="$SESSION_NAME"
        else
            TMUX_TARGET=""
        fi

        # Window 1: nvim + claude split
        tmux send-keys -t "$TMUX_TARGET" "nvim" C-m
        tmux split-window -t "$TMUX_TARGET" -h -c "$WORK_DIR" "$CLAUDE_CMD"

        # Window 2: lazygit
        tmux new-window -t "$TMUX_TARGET" -c "$WORK_DIR" -n "git" "$LAZYGIT_CMD"

        # Switch back to window 1
        tmux select-window -t "$TMUX_TARGET:1"

        # Attach if we created a new session
        if [ -z "$TMUX" ]; then
            tmux attach -t "$SESSION_NAME"
        fi
        ;;

    2)
        echo -e "${GREEN}  Creating Desktop layout (lazygit+claude in W1, nvim in W2)...${NC}"

        # Create session if not in tmux
        if [ -z "$TMUX" ]; then
            tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR"
            TMUX_TARGET="$SESSION_NAME"
        else
            TMUX_TARGET=""
        fi

        # Window 1: lazygit + claude split
        tmux send-keys -t "$TMUX_TARGET" "$LAZYGIT_CMD" C-m
        tmux split-window -t "$TMUX_TARGET" -h -c "$WORK_DIR" "$CLAUDE_CMD"

        # Window 2: nvim
        tmux new-window -t "$TMUX_TARGET" -c "$WORK_DIR" -n "nvim" "nvim"

        # Switch back to window 1
        tmux select-window -t "$TMUX_TARGET:1"

        # Attach if we created a new session
        if [ -z "$TMUX" ]; then
            tmux attach -t "$SESSION_NAME"
        fi
        ;;

    [Qq]|"")
        echo -e "${BLUE} Cancelled${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED} Invalid option: $choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN} Desktop preset created!${NC}"
echo -e ""
echo -e "  ${CYAN}Ctrl+B 1${NC} - Switch to window 1"
echo -e "  ${CYAN}Ctrl+B 2${NC} - Switch to window 2"
echo -e "  ${CYAN}Ctrl+B o${NC} - Switch between panes"
