#!/bin/bash
# SLURM job selector - SSH to Expanse, get jobs, select node, SSH to it

echo " Fetching your active SLURM jobs from Expanse..."
echo ""

# Generate TOTP for the SSH connection
export TOTP_CODE=$(oathtool --totp=SHA1 --base32 "AJW3D7MUBZGYE2B6SK6V6NCFL3S4Q2SV" 2>/dev/null)

# Use Python script to fetch jobs (more reliable than expect)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/fetch_slurm_jobs.py" ]; then
    job_data=$(python3 "$SCRIPT_DIR/fetch_slurm_jobs.py" 2>/dev/null)
else
    # Fallback to expect if Python script not available
    job_data=$(timeout 30 expect << 'EOF'
set timeout 20
set totp $env(TOTP_CODE)

spawn ssh -i ~/.ssh/id_rsa_expanse -o StrictHostKeyChecking=no -o ControlMaster=no -o ControlPath=none naglemi@login.expanse.sdsc.edu

expect {
    "*TOTP code for naglemi:*" {
        send "$totp\r"
        exp_continue
    }
    "*adjust your environment:*" {
        # MOTD finished, wait a bit for prompt then send command
        sleep 2
        send "\r"
        sleep 1
        send "sacct -u naglemi --state=RUNNING --format=JobID,JobName,NodeList --noheader\r"
        expect {
            "*naglemi@*" {
                send "exit\r"
                expect eof
            }
            timeout {
                send "exit\r"
            }
        }
    }
    timeout {
        puts "TIMEOUT waiting for MOTD"
        send "exit\r"
    }
}
EOF
    )
fi

# Debug: Show raw output
echo "DEBUG Raw output:"
echo "$job_data" | head -20
echo "---"

# Extract just the job lines
job_data=$(echo "$job_data" | grep -E "^[0-9]+" | grep -v "spawn" | grep -v "TOTP")

# Filter out batch and extern sub-jobs
job_data=$(echo "$job_data" | grep -v ".batch" | grep -v ".extern")

if [ -z "$job_data" ]; then
    echo " No jobs found at all"
    echo ""
    read -n 1 -p "Press any key to exit..."
    exit 0
fi

echo "═══════════════════════════════════════════════════════════════════"
echo "                     YOUR RUNNING SLURM JOBS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check for fzf
if command -v fzf &>/dev/null; then
    # Format and select with fzf
    selection=$(echo "$job_data" | fzf --height=15 --reverse --prompt="  Select job> " --no-info)

    if [ -n "$selection" ]; then
        # Extract node name (third column)
        # Split by spaces and get third field
        set -- $selection
        node=$3

        if [ -n "$node" ] && [ "$node" != "None" ]; then
            echo ""
            echo " Connecting to node: $node"
            echo ""

            # SSH to the node using our wrapper
            exec ~/mango/auth/ssh-wrapper "$node"
        fi
    fi
else
    # Numbered menu fallback
    echo "Your running jobs:"
    echo "───────────────────────────────────────────────────────────────────"

    # Show jobs with numbers
    count=1
    while IFS= read -r line; do
        echo "  [$count] $line"
        ((count++))
    done <<< "$job_data"

    echo "───────────────────────────────────────────────────────────────────"
    read -r -p "Enter job number (or Enter to cancel): " choice

    if [ -n "$choice" ] && [[ "$choice" =~ ^[0-9]+$ ]]; then
        # Get the selected line
        line_num=1
        selected_line=""
        while IFS= read -r line; do
            if [ "$line_num" -eq "$choice" ]; then
                selected_line="$line"
                break
            fi
            ((line_num++))
        done <<< "$job_data"

        if [ -n "$selected_line" ]; then
            # Extract node name (third column)
            # Split by spaces and get third field
            set -- $selected_line
            node=$3

            if [ -n "$node" ] && [ "$node" != "None" ]; then
                echo ""
                echo " Connecting to node: $node"
                echo ""

                # SSH to the node using our wrapper
                exec ~/mango/auth/ssh-wrapper "$node"
            fi
        fi
    fi
fi

echo "Press any key to exit..."
read -n 1