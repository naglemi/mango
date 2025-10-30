#!/bin/bash

# htop system monitoring in tmux split

# Check if htop is installed
if ! command -v htop &> /dev/null; then
    echo "htop not found, installing..."
    sudo apt-get update && sudo apt-get install -y htop
fi

# Run htop
htop