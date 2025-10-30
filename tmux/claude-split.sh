#!/bin/bash

# Quick command for Claude to split itself
# This version can be called directly with Bash tool

if [ -z "$TMUX" ]; then
    echo "Not in tmux - starting tmux first..."
    tmux new-session -d -s claude-multi
    tmux send-keys "claude --continue" C-m
    tmux split-window -h "claude --continue"
    tmux attach -t claude-multi
else
    # We're already in tmux, just split silently
    direction="${1:-h}"  # Default to horizontal split (side by side)
    
    if [ "$direction" = "h" ]; then
        tmux split-window -h -c "$(pwd)" "claude --continue"
    else
        tmux split-window -v -c "$(pwd)" "claude --continue"
    fi
fi