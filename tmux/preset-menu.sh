#!/usr/bin/env bash
# Tmux Preset Launcher Menu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│          TMUX PRESET LAUNCHER        │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[1]${NC} Desktop Preset                    ${CYAN}│${NC}"
echo -e "${CYAN}│      (nvim+claude split + lazygit)    ${CYAN}│${NC}"
echo -e "${CYAN}│                                       ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[2]${NC} Mobile Preset                     ${CYAN}│${NC}"
echo -e "${CYAN}│      (3 windows + enlarged status)    ${CYAN}│${NC}"
echo -e "${CYAN}│                                       ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Cancel                            ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Get user choice
read -n1 -p "Select preset: " choice
echo
echo

case "$choice" in
    1)
        echo -e "${GREEN}  Launching Desktop preset...${NC}"
        exec "$SCRIPT_DIR/preset-desktop.sh"
        ;;
    2)
        echo -e "${GREEN} Launching Mobile preset...${NC}"
        exec "$SCRIPT_DIR/preset-mobile.sh"
        ;;
    [Qq]|"")
        echo -e "${BLUE} Cancelled${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED} Invalid option: $choice${NC}"
        echo "Please use 1-2 or Q"
        exit 1
        ;;
esac
