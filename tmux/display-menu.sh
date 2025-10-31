#!/usr/bin/env bash
# Display Menu for Tmux (Ctrl-G / Right-click menu)
# Provides grab files and settings options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│               QUICK MENU              │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[1]${NC} NeoVim (file browser)             ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[2]${NC} Fork Claude Code                  ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[3]${NC} Tmux Presets (Desktop/Mobile)     ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[4]${NC} Grab Files (checkbox selector)    ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[5]${NC} Training (Local/EC2/Web UI)       ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[6]${NC} EC2 SSH (connect to instances)    ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[7]${NC} W&B Monitor (jobs & metrics)      ${CYAN}│${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[8]${NC} Settings (toggle options)         ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[9]${NC} Spectator Mode                    ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Quit                              ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Get user choice
read -n1 -p "Select option: " choice
echo
echo

case "$choice" in
    1)
        echo -e "${GREEN} Opening NeoVim...${NC}"
        exec nvim
        ;;
    2)
        echo -e "${GREEN} Opening Fork Claude menu...${NC}"
        exec "$SCRIPT_DIR/fork-claude-menu.sh"
        ;;
    3)
        echo -e "${GREEN} Opening Tmux Preset menu...${NC}"
        exec "$SCRIPT_DIR/preset-menu.sh"
        ;;
    4)
        echo -e "${GREEN} Starting file grab...${NC}"
        exec "$SCRIPT_DIR/grab-and-email.sh"
        ;;
    5)
        echo -e "${GREEN} Opening training launcher...${NC}"
        exec "$SCRIPT_DIR/training-launcher.sh"
        ;;
    6)
        echo -e "${GREEN}  Opening EC2 SSH menu...${NC}"
        exec "$SCRIPT_DIR/ec2-ssh-menu.sh"
        ;;
    7)
        echo -e "${GREEN} Opening W&B Monitor...${NC}"
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    8)
        echo -e "${GREEN}  Opening settings...${NC}"
        exec python3 "$SCRIPT_DIR/settings-menu.py"
        ;;
    9)
        echo -e "${GREEN}  Starting spectator mode...${NC}"
        exec "$SCRIPT_DIR/spectator.sh"
        ;;
    [Qq]|"")
        echo -e "${BLUE} Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED} Invalid option: $choice${NC}"
        echo "Please use 1-9 or Q"
        exit 1
        ;;
esac