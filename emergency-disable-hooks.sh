#!/bin/bash
# Emergency script to disable ALL Claude Code hooks

SETTINGS_FILE="$HOME/.claude/settings.json"
BACKUP_FILE="$HOME/.claude/settings.json.backup.$(date +%Y%m%d_%H%M%S)"

echo "========================================"
echo "EMERGENCY HOOK DISABLER"
echo "========================================"
echo ""

# Backup current settings
if [ -f "$SETTINGS_FILE" ]; then
    echo "Backing up current settings to:"
    echo "$BACKUP_FILE"
    cp "$SETTINGS_FILE" "$BACKUP_FILE"
    echo "✓ Backup created"
    echo ""
else
    echo "⚠ No settings file found at $SETTINGS_FILE"
    exit 1
fi

# Disable all hooks by setting to empty object
echo "Disabling all hooks..."
cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {},
  "alwaysThinkingEnabled": true
}
EOF

echo "✓ All hooks disabled"
echo ""
echo "Settings file updated: $SETTINGS_FILE"
echo ""
echo "To restore hooks, copy backup back:"
echo "  cp $BACKUP_FILE $SETTINGS_FILE"
echo ""
echo "You may need to restart Claude Code for changes to take effect."
echo ""
echo "========================================"
