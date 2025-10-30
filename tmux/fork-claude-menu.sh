#!/usr/bin/env bash
# Fork Claude Code with options menu

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│          FORK CLAUDE CODE            │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[1]${NC} Continue (safe mode)               ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[2]${NC} Continue (skip permissions)        ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[3]${NC} Resume (safe mode)                 ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[4]${NC} Resume (skip permissions)          ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Cancel                             ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo
echo -e "${YELLOW}Note: Skip permissions = --dangerously-skip-permissions${NC}"
echo

# Get user choice
read -n1 -p "Select option: " choice
echo
echo

# Check if we're in tmux
if [ -z "$TMUX" ]; then
    echo -e "${RED} Not in tmux session${NC}"
    exit 1
fi

# Get current pane's working directory
PANE_DIR="$(tmux display-message -p '#{pane_current_path}')"

case "$choice" in
    1)
        echo -e "${GREEN} Forking Claude Code (continue, safe)...${NC}"
        tmux split-window -h -c "$PANE_DIR" "claude --continue"
        ;;
    2)
        echo -e "${YELLOW} Forking Claude Code (continue, skip permissions)...${NC}"
        tmux split-window -h -c "$PANE_DIR" "claude --continue --dangerously-skip-permissions"
        ;;
    3)
        echo -e "${GREEN} Forking Claude Code (resume, safe)...${NC}"
        tmux split-window -h -c "$PANE_DIR" "claude --resume"
        ;;
    4)
        echo -e "${YELLOW} Forking Claude Code (resume, skip permissions)...${NC}"
        tmux split-window -h -c "$PANE_DIR" "claude --resume --dangerously-skip-permissions"
        ;;
    [Qq]|"")
        echo -e "${BLUE} Cancelled${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED} Invalid option: $choice${NC}"
        echo "Please use 1-4 or Q"
        exit 1
        ;;
esac
