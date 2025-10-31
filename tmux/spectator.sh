#!/usr/bin/env bash
# Standalone Spectator Mode - Live file monitoring with vim-gitgutter
# Can be called from anywhere as 'spectator' command

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Capture the actual working directory
WORK_DIR="${1:-$(pwd)}"

# Check if already in tmux
if [ -n "$TMUX" ]; then
    # We're already in tmux, run the split version directly in the correct directory
    cd "$WORK_DIR" || cd "$(pwd)"
    exec "$SCRIPT_DIR/spectator-split.sh"
else
    # Not in tmux, create new session and run spectator
    cd "$WORK_DIR" || exit 1

    # Create a unique session name
    SESSION_NAME="spectator-$(date +%s)"

    # Start new tmux session with spectator
    exec tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR" "$SCRIPT_DIR/spectator-split.sh" \; attach-session -t "$SESSION_NAME"
fi