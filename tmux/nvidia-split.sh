#!/bin/bash

# nvidia-smi monitoring in tmux split
# Auto-refreshes every 2 seconds

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "nvidia-smi not found"
    echo "NVIDIA drivers may not be installed"
    read -p "Press Enter to exit..."
    exit 1
fi

# Run nvidia-smi in watch mode for continuous monitoring
watch -n 2 nvidia-smi