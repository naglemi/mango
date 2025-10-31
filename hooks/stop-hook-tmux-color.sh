#!/usr/bin/env bash
# Stop hook: Change tmux pane background to idle color when Claude finishes responding
# Hook Type: Stop
# Purpose: Visual feedback that Claude is idle and ready for next input
#
# Contract:
# - Input: JSON via stdin with session_id, hook_event_name
# - Output: Exit 0 always (never block Claude)
# - Side Effect: Changes tmux pane background color via `tmux select-pane`
# - Performance: <100ms execution time

# Read JSON input from stdin
INPUT=$(cat)

# Check if feature is enabled in settings
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    ENABLED=$(jq -r '.tmux_color_notifications_enabled // false' "$SETTINGS_FILE" 2>/dev/null)
    if [ "$ENABLED" != "true" ]; then
        exit 0
    fi
    IDLE_COLOR=$(jq -r '.tmux_idle_color // "green"' "$SETTINGS_FILE" 2>/dev/null)
else
    # Settings file missing, feature not enabled by default
    exit 0
fi

# Check if running in tmux
if [ -z "${TMUX_PANE:-}" ]; then
    # Not in tmux, exit gracefully
    exit 0
fi

# Change pane background to idle color
tmux select-pane -t "$TMUX_PANE" -P "bg=$IDLE_COLOR" > /dev/null 2>&1

# Always exit 0 (never block Claude)
exit 0
