#!/usr/bin/env bash
# Training Launcher Menu - Unified interface for Local and EC2 training
# Uses the same backend as Web UI for consistency

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/home/ubuntu/finetune_safe"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
DIM='\033[2m'

# Check if we're in or can access finetune_safe project
check_project() {
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED} Project directory not found: $PROJECT_DIR${NC}"
        echo "The finetune_safe project is required for training."
        read -p "Press Enter to exit..."
        exit 1
    fi
}

# Show training launcher menu
show_menu() {
    clear
    echo -e "${CYAN}╭─────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│             TRAINING LAUNCHER                 │${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│  ${GREEN}[1]${NC} Local Training (Current GPU)              ${CYAN}│${NC}"
    echo -e "${CYAN}│  ${GREEN}[2]${NC} EC2 Batch Launch (Multiple Configs)       ${CYAN}│${NC}"
    echo -e "${CYAN}│  ${GREEN}[3]${NC} Web UI Control Center (Full Interface)    ${CYAN}│${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│  ${YELLOW}[C]${NC} Check Status (Local & EC2)                ${CYAN}│${NC}"
    echo -e "${CYAN}│  ${YELLOW}[I]${NC} EC2 Instance Details                      ${CYAN}│${NC}"
    echo -e "${CYAN}│  ${YELLOW}[L]${NC} View Latest Logs                         ${CYAN}│${NC}"
    echo -e "${CYAN}│  ${YELLOW}[D]${NC} Open W&B Dashboard                       ${CYAN}│${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│  ${RED}[Q]${NC} Quit                                      ${CYAN}│${NC}"
    echo -e "${CYAN}╰─────────────────────────────────────────────────╯${NC}"
    echo
}

# Launch local training using existing menu
launch_local_training() {
    echo -e "${GREEN}  Starting local training menu...${NC}"
    cd "$PROJECT_DIR" || exit 1

    # Check if configs directory exists
    if [ ! -d "configs" ]; then
        echo -e "${RED} Error: configs directory not found${NC}"
        read -p "Press Enter to return to menu..."
        return
    fi

    # Get list of config files
    configs=$(ls -1 configs/*.yaml 2>/dev/null | sed 's|configs/||' | sed 's|\.yaml||')

    if [ -z "$configs" ]; then
        echo -e "${YELLOW}  No config files found in configs/${NC}"
        read -p "Press Enter to return to menu..."
        return
    fi

    # Use fzf for interactive selection with fuzzy search
    if command -v fzf &>/dev/null; then
        echo -e "${CYAN} Select a training configuration (type to filter):${NC}"
        echo

        config_name=$(echo "$configs" | fzf \
            --height=20 \
            --border=rounded \
            --prompt="Config: " \
            --header="Type to filter configs, Enter to select, Esc to cancel" \
            --preview="echo 'Config: {}.yaml' && echo && bat --color=always --style=plain configs/{}.yaml 2>/dev/null || cat configs/{}.yaml 2>/dev/null" \
            --preview-window=right:60% \
            --color="border:cyan,prompt:green,header:blue")

        if [ -z "$config_name" ]; then
            echo -e "${BLUE} No config selected. Returning to menu.${NC}"
            sleep 1
            return
        fi
    else
        # Fallback to numbered list if fzf not available
        echo -e "${CYAN}Available configurations:${NC}"
        echo "$configs" | nl
        echo
        read -p "Enter config name (without .yaml): " config_name

        if [ -z "$config_name" ]; then
            echo -e "${BLUE} No config provided. Returning to menu.${NC}"
            sleep 1
            return
        fi
    fi

    # Launch training
    echo
    echo -e "${GREEN} Launching training with config: ${config_name}.yaml${NC}"
    echo
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate fresh
    python main.py --objective-config "configs/${config_name}.yaml"
}

# EC2 batch launch using the same backend as Web UI
launch_ec2_batch() {
    echo -e "${GREEN} EC2 Batch Training Launch${NC}"
    echo
    cd "$PROJECT_DIR" || exit 1

    # Check AWS credentials first
    echo -e "${CYAN}Checking AWS setup...${NC}"
    aws_check=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from web_ui_components.ec2_launcher import check_aws_setup
    aws_status, ami_status, ready = check_aws_setup()
    print(f'{aws_status}|{ami_status}|{ready}')
except Exception as e:
    print(f'Error: {e}|Error|False')
" 2>/dev/null)

    IFS='|' read -r aws_status ami_status ready <<< "$aws_check"

    echo "$aws_status"
    echo "$ami_status"

    if [[ "$ready" != "True" ]]; then
        echo
        echo -e "${YELLOW}AWS setup is not ready. Please:${NC}"
        echo "  1. Configure AWS credentials: source ./aws_credentials.sh"
        echo "  2. Create an AMI if needed (use Web UI option 3)"
        echo
        read -p "Press Enter to return to menu..."
        return
    fi

    echo
    echo -e "${CYAN}Enter config names (one per line, press Ctrl+D when done):${NC}"
    echo -e "${DIM}Example configs:${NC}"
    echo -e "${DIM}  mo_mgda${NC}"
    echo -e "${DIM}  mo_pcgrad${NC}"
    echo -e "${DIM}  decor3_mgda${NC}"
    echo

    # Collect config names
    configs=""
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            configs="${configs}${line}\n"
        fi
    done

    if [ -z "$configs" ]; then
        echo -e "${YELLOW}No configs provided. Returning to menu...${NC}"
        sleep 2
        return
    fi

    # Remove trailing newline
    configs=$(echo -e "$configs" | sed '/^$/d')

    # Ask for spot vs on-demand
    echo
    echo -e "${CYAN}Instance type:${NC}"
    echo "  [1] On-demand (reliable, default)"
    echo "  [2] Spot instances (70% savings, may be interrupted)"
    read -n1 -p "Choice [1]: " instance_choice
    echo

    if [ "$instance_choice" == "2" ]; then
        use_spot="True"
        instance_type="Spot"
    else
        use_spot="False"
        instance_type="On-Demand"
    fi

    # Show cost estimate
    num_configs=$(echo -e "$configs" | wc -l)
    echo
    echo -e "${CYAN}Cost Estimate:${NC}"
    python3 -c "
import sys
sys.path.insert(0, '.')
from web_ui_components.ec2_launcher import estimate_ec2_cost
estimate = estimate_ec2_cost($num_configs, 6.0, $use_spot)
print(estimate)
"

    echo
    read -p "Launch $num_configs $instance_type instances? [y/N]: " confirm

    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        echo -e "${YELLOW}Launch cancelled${NC}"
        sleep 2
        return
    fi

    # Launch using the same backend as Web UI
    echo
    echo -e "${GREEN}Launching EC2 instances...${NC}"

    result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from web_ui_components.ec2_launcher import launch_ec2_training

configs = '''$configs'''
use_spot = $use_spot

result = launch_ec2_training(configs, use_spot, parallel=True)
print(result)
" 2>&1)

    echo "$result"
    echo
    read -p "Press Enter to return to menu..."
}

# Open Web UI
open_web_ui() {
    echo -e "${GREEN} Starting Web UI Control Center...${NC}"
    cd "$PROJECT_DIR" || exit 1

    # Check if web UI is already running
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}Web UI is already running on port 8080${NC}"
        echo -e "${CYAN}Access it at: http://localhost:8080${NC}"

        # Try to get public IP for remote access
        public_ip=$(curl -s ifconfig.me 2>/dev/null)
        if [ -n "$public_ip" ]; then
            echo -e "${DIM}Remote access: http://${public_ip}:8080${NC}"
        fi
    else
        echo -e "${CYAN}Starting Enhanced Web UI with full EC2 support...${NC}"

        # Start in background with proper logging
        nohup python3 web_ui_enhanced.py > /tmp/webui.log 2>&1 &
        webui_pid=$!

        sleep 3

        # Check if it started successfully
        if kill -0 $webui_pid 2>/dev/null; then
            echo -e "${GREEN} Web UI started successfully!${NC}"
            echo -e "${CYAN}Local access: http://localhost:8080${NC}"

            public_ip=$(curl -s ifconfig.me 2>/dev/null)
            if [ -n "$public_ip" ]; then
                echo -e "${DIM}Remote access: http://${public_ip}:8080${NC}"
            fi
            echo -e "${DIM}Logs: /tmp/webui.log${NC}"
        else
            echo -e "${RED} Failed to start Web UI${NC}"
            echo "Check logs at /tmp/webui.log"
            tail -20 /tmp/webui.log
        fi
    fi

    echo
    read -p "Press Enter to return to menu..."
}

# Check status (unified for local and EC2)
check_status() {
    echo -e "${BLUE} Training Status${NC}"
    echo "═══════════════════════════════════════════════════"

    # Check local processes
    echo -e "${CYAN}Local Training Processes:${NC}"
    if pgrep -f "python main.py" > /dev/null; then
        ps aux | grep "python main.py" | grep -v grep | awk '{print "  PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%", "| Time:", $10}'
    else
        echo "  No local training running"
    fi
    echo

    # Check EC2 instances using the same backend as Web UI
    echo -e "${CYAN}EC2 Training Instances:${NC}"
    cd "$PROJECT_DIR" || exit 1
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from web_ui_components.ec2_launcher import get_ec2_status
    status = get_ec2_status()
    print(status)
except Exception as e:
    print(f'  Error checking EC2 status: {e}')
" 2>/dev/null

    echo
    read -p "Press Enter to continue..."
}

# EC2-specific status (more detailed)
check_ec2_status() {
    echo -e "${BLUE} Detailed EC2 Instance Status${NC}"
    echo "═══════════════════════════════════════════════════"

    cd "$PROJECT_DIR" || exit 1

    # Get detailed status using the EC2 launcher
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from web_ui_components.ec2_launcher import EC2LauncherComponent

    launcher = EC2LauncherComponent()
    if not launcher.credentials_valid:
        print(' AWS credentials not configured')
        print('Run: source ./aws_credentials.sh')
    else:
        instances = launcher.get_running_instances()
        if instances:
            print('Running EC2 Training Instances:\n')
            print(f'{'Instance ID':<20} {'Config':<20} {'State':<10} {'Launch Time':<20} {'IP':<15}')
            print('-' * 85)
            for inst in instances:
                print(f\"{inst['instance_id']:<20} {inst['config']:<20} {inst['state']:<10} {inst['launch_time'][:19]:<20} {inst['public_ip']:<15}\")

            print(f'\nTotal: {len(instances)} instances')

            # Cost estimate
            from web_ui_components.ec2_launcher import estimate_ec2_cost
            # Assume average 4 hours remaining, 70% are spot
            spot_count = int(len(instances) * 0.7)
            ondemand_count = len(instances) - spot_count

            if spot_count > 0:
                spot_cost = estimate_ec2_cost(spot_count, 4, True)
                print(f'\nEstimated remaining cost (spot): ~$' + spot_cost.split('$')[-1].split('**')[0] + '/hour')
            if ondemand_count > 0:
                ondemand_cost = estimate_ec2_cost(ondemand_count, 4, False)
                print(f'Estimated remaining cost (on-demand): ~$' + ondemand_cost.split('$')[-1].split('**')[0] + '/hour')
        else:
            print('No EC2 training instances currently running')

except Exception as e:
    print(f'Error: {e}')
" 2>&1

    echo
    echo -e "${CYAN}Options:${NC}"
    echo "  [T] Terminate an instance"
    echo "  [R] Refresh status"
    echo "  [B] Back to main menu"
    echo

    read -n1 -p "Choice: " ec2_choice
    echo

    case "$ec2_choice" in
        [Tt])
            echo
            read -p "Enter Instance ID to terminate: " instance_id
            if [ -n "$instance_id" ]; then
                python3 -c "
import sys
sys.path.insert(0, '.')
from web_ui_components.ec2_launcher import terminate_ec2_instance
result = terminate_ec2_instance('$instance_id')
print(result)
"
                sleep 2
            fi
            check_ec2_status
            ;;
        [Rr])
            check_ec2_status
            ;;
        *)
            return
            ;;
    esac
}

# View latest logs
view_logs() {
    echo -e "${BLUE} Latest Training Logs${NC}"
    echo "═══════════════════════════════════════════════════"

    LOG_DIR="$PROJECT_DIR/logs"
    if [ -d "$LOG_DIR" ]; then
        # Find most recent log file
        latest_log=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            echo -e "${GREEN}Latest log: $(basename "$latest_log")${NC}"
            echo -e "${DIM}Modified: $(date -r "$latest_log" '+%Y-%m-%d %H:%M:%S')${NC}"
            echo
            tail -n 50 "$latest_log"
            echo
            echo "═══════════════════════════════════════════════════"
            read -p "View full log? [y/N]: " view_full
            if [[ "$view_full" == "y" ]]; then
                less "$latest_log"
            fi
        else
            echo -e "${YELLOW}No log files found in $LOG_DIR${NC}"
        fi
    else
        echo -e "${RED}Log directory not found: $LOG_DIR${NC}"
    fi

    echo
    read -p "Press Enter to continue..."
}

# Open W&B dashboard
open_wandb() {
    echo -e "${BLUE} Opening W&B Dashboard...${NC}"

    # Try to get the actual project from recent runs
    project_url="https://wandb.ai"

    cd "$PROJECT_DIR" || exit 1
    wandb_project=$(python3 -c "
try:
    import yaml
    # Try to get project from a config file
    with open('configs/mo_mgda.yaml', 'r') as f:
        config = yaml.safe_load(f)
        project = config.get('wandb_project', 'cluster-pareto-grpo-safe')
        print(f'https://wandb.ai/your-team/{project}')
except:
    print('https://wandb.ai')
" 2>/dev/null)

    if [ -n "$wandb_project" ]; then
        project_url="$wandb_project"
    fi

    echo "W&B Dashboard: $project_url"

    if command -v xdg-open &> /dev/null; then
        xdg-open "$project_url" 2>/dev/null
        echo "Opened in browser"
    else
        echo "Please open in your browser: $project_url"
    fi

    echo
    read -p "Press Enter to continue..."
}

# Main menu loop
main() {
    check_project

    while true; do
        show_menu
        read -n1 -p "Select option: " choice
        echo
        echo

        case "$choice" in
            1)
                launch_local_training
                ;;
            2)
                launch_ec2_batch
                ;;
            3)
                open_web_ui
                ;;
            [Cc])
                check_status
                ;;
            [Ii])
                check_ec2_status
                ;;
            [Ll])
                view_logs
                ;;
            [Dd])
                open_wandb
                ;;
            [Qq])
                echo -e "${BLUE} Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED} Invalid option: $choice${NC}"
                echo "Please select a valid option"
                sleep 2
                ;;
        esac
    done
}

# Run the menu
main