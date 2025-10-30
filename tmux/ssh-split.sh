#!/bin/bash

# SSH host selector for tmux split
# Shows numbered list of hosts from SSH config

# Extract hosts from SSH config
hosts=$(grep "^Host " ~/.ssh/config 2>/dev/null | grep -v "*" | cut -d' ' -f2 | sort -u)

if [ -z "$hosts" ]; then
    echo "No SSH hosts found in ~/.ssh/config"
    read -p "Press Enter to exit..."
    exit 1
fi

# Create numbered list
echo "=== SSH Host Selector ==="
echo
i=1
host_array=()
while IFS= read -r host; do
    echo "  $i) $host"
    host_array+=("$host")
    ((i++))
done <<< "$hosts"

echo
echo -n "Select host (1-$((i-1))) or q to quit: "
read -r selection

if [[ "$selection" == "q" ]]; then
    exit 0
fi

if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -lt "$i" ]; then
    selected_host="${host_array[$((selection-1))]}"
    clear
    echo "Connecting to $selected_host..."
    ssh "$selected_host"
else
    echo "Invalid selection"
    sleep 1
fi