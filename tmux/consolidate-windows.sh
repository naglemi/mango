#!/usr/bin/env bash
# Combine ALL windows into one window with all panes
# Simple, no options, just do it

set -euo pipefail

session_name=$(tmux display-message -p '#S')

# Check we're in tmux
if [ -z "$TMUX" ]; then
    echo "Error: Must run from within tmux" >&2
    exit 1
fi

# Get all windows
all_windows=$(tmux list-windows -t "$session_name" -F "#{window_index}")

if [ -z "$all_windows" ]; then
    echo "Error: No windows found" >&2
    exit 1
fi

window_array=($all_windows)
window_count=${#window_array[@]}

if [ "$window_count" -lt 2 ]; then
    echo "Only 1 window - nothing to combine"
    sleep 2
    exit 0
fi

clear
echo "COMBINE ALL WINDOWS"
echo ""
echo "Found $window_count windows"
echo "This will combine everything into one window"
echo ""
read -n 1 -p "Continue? [Y/n]: " confirm
echo ""

if [[ "$confirm" =~ ^[Nn] ]]; then
    exit 0
fi

# Use first window as target
target_window="${window_array[0]}"
tmux rename-window -t ":$target_window" "Combined"

# Move all panes from all other windows
for win in "${window_array[@]:1}"; do
    panes=$(tmux list-panes -t "$session_name:$win" -F "#{pane_index}")
    for pane in $panes; do
        tmux join-pane -s "$session_name:$win.$pane" -t ":$target_window" 2>/dev/null || true
    done
    tmux kill-window -t ":$win" 2>/dev/null || true
done

# Apply tiled layout
tmux select-window -t ":$target_window"
tmux select-layout -t ":$target_window" tiled

clear
echo "DONE"
echo ""
echo "All windows combined into window $target_window"
sleep 2
