#!/bin/bash
# Single installation script for Claude Pushover notifications
# This installs the Stop hook that sends notifications when Claude finishes responding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/stop-hook-pushover.py"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing Claude Pushover Notification Hook"
echo "==========================================="
echo ""

# Check environment variables
if [ -z "$PUSHOVER_APP_TOKEN" ] || [ -z "$PUSHOVER_USER_KEY" ]; then
    echo "  WARNING: Pushover environment variables not found!"
    echo "   Please ensure these are set in your ~/.bashrc:"
    echo "   export PUSHOVER_APP_TOKEN='your-app-token'"
    echo "   export PUSHOVER_USER_KEY='your-user-key'"
    echo ""
fi

# Ensure the hook script exists
if [ ! -f "$HOOK_SCRIPT" ]; then
    echo " Error: Hook script not found: $HOOK_SCRIPT"
    exit 1
fi

# Make hook executable
chmod +x "$HOOK_SCRIPT"

# Make sure settings directory exists
mkdir -p "$HOME/.claude"

# Check if settings.json exists
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "Creating new settings.json..."
    echo '{}' > "$SETTINGS_FILE"
fi

# Check for jq
if ! command -v jq >/dev/null 2>&1; then
    echo " Error: jq is required for installation"
    echo "   Install with: sudo apt-get install jq"
    exit 1
fi

# Create the hook configuration
echo "Configuring Stop hook..."
HOOK_CONFIG=$(cat <<EOF
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$HOOK_SCRIPT"
          }
        ]
      }
    ]
  }
}
EOF
)

# Merge with existing settings
jq -s '.[0] * .[1]' "$SETTINGS_FILE" <(echo "$HOOK_CONFIG") > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"

echo " Hook installed successfully!"
echo ""
echo "What this does:"
echo "  • Sends a Pushover notification when Claude finishes responding"
echo "  • Notification includes: hostname: message content"
echo "  • If a report was sent, includes the report URL"
echo "  • Title shows: folder_name [session_id]"
echo ""
echo "To verify installation:"
echo "  • Run: /hooks (in Claude)"
echo "  • Check: cat ~/.claude/settings.json"
echo ""
echo "To test:"
echo "  • Ask Claude anything and check your Pushover app"
echo "  • Debug log: tail -f /tmp/stop-hook-debug.log"
echo ""
echo "  IMPORTANT: Restart Claude Code for the hook to take effect!"
echo ""