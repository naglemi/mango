#!/usr/bin/env bash
# W&B Monitor Menu for Tmux
# Provides quick access to W&B monitoring features

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│            W&B MONITOR                │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────┤${NC}"
echo -e "${CYAN}│  ${GREEN}[1]${NC} Quick Status (Local+EC2+W&B)     ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[2]${NC} EC2 Failure Logs (last failed)   ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[3]${NC} List Projects                     ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[4]${NC} Show Running Jobs                 ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[5]${NC} Show All Jobs (with configs)     ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[6]${NC} EC2 Training Status               ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[7]${NC} Local Process Status (Real)       ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[8]${NC} Get Run Metrics (by ID)           ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[9]${NC} Interactive Mode                  ${CYAN}│${NC}"
echo -e "${CYAN}│  ${GREEN}[Q]${NC} Back to Main Menu                 ${CYAN}│${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Get user choice
read -n1 -p "Select option: " choice
echo
echo

# Navigate to the finetune_safe directory where wandb_tools is located
cd /home/ubuntu/finetune_safe

# Activate fresh conda environment (required for wandb)
source ~/miniconda3/etc/profile.d/conda.sh
conda activate fresh

case "$choice" in
    1)
        echo -e "${GREEN} Getting complete training status...${NC}"
        /home/ubuntu/finetune_safe/status all
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    2)
        echo -e "${RED} Getting failure logs from most recent terminated EC2...${NC}"
        /home/ubuntu/finetune_safe/status logs
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    3)
        echo -e "${GREEN} Fetching W&B projects...${NC}"
        python3 -m wandb_tools.cli.monitor projects
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    4)
        echo -e "${GREEN} Fetching running jobs...${NC}"
        python3 -m wandb_tools.cli.monitor jobs --running
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    5)
        echo -e "${GREEN} Fetching all jobs with configs...${NC}"
        python3 -m wandb_tools.cli.monitor jobs
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    6)
        echo -e "${GREEN}  Checking EC2 training instances...${NC}"
        python3 -m wandb_tools.cli.monitor ec2
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    7)
        echo -e "${GREEN} Checking actual local processes (not shell sessions)...${NC}"
        python3 -m wandb_tools.cli.monitor local
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    8)
        echo -e "${MAGENTA}Enter W&B run ID:${NC} "
        read run_id
        if [ -n "$run_id" ]; then
            echo -e "${GREEN} Fetching metrics for run: $run_id${NC}"
            python3 -m wandb_tools.cli.monitor metrics "$run_id"
        else
            echo -e "${RED} No run ID provided${NC}"
        fi
        echo
        echo -e "${YELLOW}Press any key to continue...${NC}"
        read -n1
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    9)
        echo -e "${GREEN} Starting interactive mode...${NC}"
        echo -e "${YELLOW}(Use menu options to navigate, Q to exit interactive mode)${NC}"
        echo
        python3 -m wandb_tools.cli.monitor interactive
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
    [Qq]|"")
        echo -e "${BLUE}↩  Returning to main menu...${NC}"
        exec "$SCRIPT_DIR/display-menu.sh"
        ;;
    *)
        echo -e "${RED} Invalid option: $choice${NC}"
        echo "Please use 1-9 or Q"
        sleep 2
        exec "$SCRIPT_DIR/wandb-monitor.sh"
        ;;
esac