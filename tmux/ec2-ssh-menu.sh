#!/usr/bin/env bash
# EC2 SSH Menu - List running EC2 instances and SSH into selected one
# Uses AWS credentials from aws_credentials.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AWS_CREDS_SCRIPT="/home/ubuntu/mango/aws_credentials.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load AWS credentials
if [[ -f "$AWS_CREDS_SCRIPT" ]]; then
    echo -e "${CYAN} Loading AWS credentials...${NC}"
    source "$AWS_CREDS_SCRIPT"
else
    echo -e "${RED} Error: AWS credentials file not found at $AWS_CREDS_SCRIPT${NC}"
    exit 1
fi

echo
echo -e "${CYAN}╭─────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│           EC2 SSH CONNECTOR          │${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────╯${NC}"
echo

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo -e "${RED} Error: AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Fetch running EC2 instances with their IPs and names
echo -e "${YELLOW} Fetching running EC2 instances...${NC}"
echo

# Query AWS for running instances - get instance ID, name tag, public IP, and private IP
instances=$(aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress,PrivateIpAddress,InstanceType]' \
    --output text 2>&1)

if [[ $? -ne 0 ]]; then
    echo -e "${RED} Error fetching EC2 instances:${NC}"
    echo "$instances"
    exit 1
fi

if [[ -z "$instances" || "$instances" == "None" ]]; then
    echo -e "${YELLOW}  No running EC2 instances found.${NC}"
    echo
    read -p "Press Enter to return to menu..."
    exit 0
fi

# Format instances for display and selection
# Format: "InstanceID | Name | PublicIP | PrivateIP | Type"
formatted_instances=""
while IFS=$'\t' read -r instance_id name public_ip private_ip instance_type; do
    # Handle missing values
    [[ -z "$name" || "$name" == "None" ]] && name="<unnamed>"
    [[ -z "$public_ip" || "$public_ip" == "None" ]] && public_ip="<no-public-ip>"
    [[ -z "$private_ip" || "$private_ip" == "None" ]] && private_ip="<no-private-ip>"
    [[ -z "$instance_type" ]] && instance_type="unknown"

    # Format for display
    formatted_line=$(printf "%-19s | %-30s | %-15s | %-15s | %s" \
        "$instance_id" "$name" "$public_ip" "$private_ip" "$instance_type")

    if [[ -n "$formatted_instances" ]]; then
        formatted_instances="$formatted_instances"$'\n'"$formatted_line"
    else
        formatted_instances="$formatted_line"
    fi
done <<< "$instances"

# Check if fzf is available
if ! command -v fzf &> /dev/null; then
    echo -e "${RED} Error: fzf not found. Please install it first.${NC}"
    echo
    echo "Running instances:"
    echo "$formatted_instances"
    exit 1
fi

# Display instances in fzf menu
echo -e "${GREEN} Select an instance to SSH into:${NC}"
echo

selected=$(echo "$formatted_instances" | fzf \
    --height=20 \
    --border=rounded \
    --prompt="SSH to: " \
    --header="Instance ID          | Name                           | Public IP       | Private IP      | Type" \
    --preview-window=hidden \
    --color="border:cyan,prompt:green,header:blue")

if [[ -z "$selected" ]]; then
    echo -e "${BLUE} No instance selected. Returning to menu.${NC}"
    exit 0
fi

# Extract the IPs from selected line
public_ip=$(echo "$selected" | awk -F'|' '{print $3}' | xargs)
private_ip=$(echo "$selected" | awk -F'|' '{print $4}' | xargs)
instance_name=$(echo "$selected" | awk -F'|' '{print $2}' | xargs)
instance_id=$(echo "$selected" | awk -F'|' '{print $1}' | xargs)

# Determine which IP to use (prefer public, fallback to private)
target_ip=""
if [[ "$public_ip" != "<no-public-ip>" ]]; then
    target_ip="$public_ip"
    ip_type="public"
elif [[ "$private_ip" != "<no-private-ip>" ]]; then
    target_ip="$private_ip"
    ip_type="private"
else
    echo -e "${RED} Error: No valid IP address found for instance $instance_id${NC}"
    exit 1
fi

echo
echo -e "${GREEN} Connecting to instance:${NC}"
echo -e "  ${CYAN}Name:${NC} $instance_name"
echo -e "  ${CYAN}Instance ID:${NC} $instance_id"
echo -e "  ${CYAN}IP ($ip_type):${NC} $target_ip"
echo

# Prompt for username (default to ubuntu)
read -p "Username [ubuntu]: " username
username=${username:-ubuntu}

# SSH key path (adjust as needed)
echo
read -p "SSH key path [~/.ssh/id_rsa]: " ssh_key
ssh_key=${ssh_key:-~/.ssh/id_rsa}

# Expand tilde
ssh_key="${ssh_key/#\~/$HOME}"

if [[ ! -f "$ssh_key" ]]; then
    echo -e "${YELLOW}  Warning: SSH key not found at $ssh_key${NC}"
    echo -e "${YELLOW}Attempting connection without explicit key...${NC}"
    ssh_cmd="ssh ${username}@${target_ip}"
else
    ssh_cmd="ssh -i ${ssh_key} ${username}@${target_ip}"
fi

echo
echo -e "${GREEN} Executing: ${CYAN}$ssh_cmd${NC}"
echo
sleep 1

# Execute SSH
exec $ssh_cmd
