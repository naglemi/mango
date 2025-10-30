#!/bin/bash
# Divide panes into two rows, creating a new pane if there's only one

# Get the number of panes in the current window
num_panes=$(tmux list-panes | wc -l)

if [ "$num_panes" -eq 1 ]; then
    # If only one pane, split it horizontally to create two rows
    tmux split-window -v -c "#{pane_current_path}"
    tmux display-message "Split into two rows (added new pane)"
else
    # Use the tiled layout which arranges panes in a grid
    # This will distribute panes evenly into rows
    tmux select-layout tiled
    tmux display-message "Panes arranged into rows"
fi
