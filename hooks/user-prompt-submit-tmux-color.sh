#!/usr/bin/env bash
# UserPromptSubmit hook: Reset tmux pane background to active color when user submits input
# Hook Type: UserPromptSubmit
# Purpose: Visual feedback that Claude is actively processing user's input
#
# Contract:
# - Input: JSON via stdin with session_id, user_prompt, hook_event_name
# - Output: Exit 0 always (never block Claude)
# - Side Effect: Resets tmux pane background color via `tmux select-pane`
# - Performance: <50ms execution time (critical - fires before processing starts)

# Read JSON input from stdin
INPUT=$(cat)

# Check if feature is enabled in settings
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    ENABLED=$(jq -r '.tmux_color_notifications_enabled // false' "$SETTINGS_FILE" 2>/dev/null)
    if [ "$ENABLED" != "true" ]; then
        exit 0
    fi
    ACTIVE_COLOR=$(jq -r '.tmux_active_color // "default"' "$SETTINGS_FILE" 2>/dev/null)
else
    # Settings file missing, feature not enabled by default
    exit 0
fi

# Check if running in tmux
if [ -z "${TMUX_PANE:-}" ]; then
    # Not in tmux, exit gracefully
    exit 0
fi

# Reset pane background to active color
tmux select-pane -t "$TMUX_PANE" -P "bg=$ACTIVE_COLOR" > /dev/null 2>&1

# Always exit 0 (never block Claude)
exit 0
