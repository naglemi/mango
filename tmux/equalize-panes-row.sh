#!/bin/bash
# Equalize all panes in current window into equal widths on one row

# Select the even-horizontal layout which distributes panes equally horizontally
tmux select-layout even-horizontal

# Display confirmation
tmux display-message "Panes equalized in one row"
