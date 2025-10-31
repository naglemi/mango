#!/bin/bash
set -euo pipefail

# Generate final tmux.conf from template and menu configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/tmux.conf.template"
MENU_CONFIG="$HOME/.tmux-menu-config.txt"
SETTINGS_FILE="$HOME/.claude/settings.json"
OUTPUT="$HOME/.tmux.conf"

# Check if menu configuration exists
if [ ! -f "$MENU_CONFIG" ]; then
    echo "ERROR: Menu configuration not found at $MENU_CONFIG"
    echo "Please run configure-menu.py first"
    exit 1
fi

# Read menu items
MENU_ITEMS=$(cat "$MENU_CONFIG")

# Read template and replace placeholder
if [ ! -f "$TEMPLATE" ]; then
    echo "ERROR: Template not found at $TEMPLATE"
    exit 1
fi

# Check if close pane confirmation should be skipped
SKIP_CLOSE_CONFIRM="false"
if [ -f "$SETTINGS_FILE" ]; then
    SKIP_CLOSE_CONFIRM=$(jq -r '.skip_close_pane_confirmation // false' "$SETTINGS_FILE" 2>/dev/null || echo "false")
fi

# Generate close pane command based on setting
if [ "$SKIP_CLOSE_CONFIRM" = "true" ]; then
    CLOSE_PANE_CMD="kill-pane"
else
    CLOSE_PANE_CMD="display-menu -T 'Close Pane?' 'Yes (Kill)' z 'kill-pane' 'Break to Window' p 'break-pane' 'Suspend' q 'send-keys C-z' 'No (Cancel)' n ''"
fi

# Replace placeholders with actual content
while IFS= read -r line; do
    if [[ "$line" == *"{{MENU_ITEMS}}"* ]]; then
        echo "$MENU_ITEMS"
    elif [[ "$line" == *"{{CLOSE_PANE_CMD}}"* ]]; then
        echo "${line//\{\{CLOSE_PANE_CMD\}\}/$CLOSE_PANE_CMD}"
    else
        printf '%s\n' "$line"
    fi
done < "$TEMPLATE" > "$OUTPUT"

echo " Generated $OUTPUT from template"
echo " Configured menu with your selections"

# Generate mobile menu pages
echo ""
echo "Generating mobile menu configuration..."
bash "$SCRIPT_DIR/generate-mobile-menu.sh"
