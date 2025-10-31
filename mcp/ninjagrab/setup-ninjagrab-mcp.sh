#!/bin/bash

# Setup script for ninjagrab MCP
# Provides file collection functionality via MCP instead of CLI calls

set -e

echo "Setting up ninjagrab MCP for Claude Code..."

# Get current directory for absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANGO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Remove existing ninjagrab configuration if it exists
echo "Removing any existing ninjagrab MCP configuration..."
claude mcp remove ninjagrab 2>/dev/null || true

# Ensure ninjagrab.sh is available
if [ ! -f "$MANGO_ROOT/ninjagrab.sh" ]; then
    echo -e "ninjagrab.sh not found in $MANGO_ROOT"
    echo "     MCP will use Python fallback implementation"
fi

# Add ninjagrab MCP using claude mcp CLI
echo "Registering ninjagrab MCP with Claude Code..."
if claude mcp add ninjagrab -s project -e NINJAGRAB_SCRIPT_PATH="$MANGO_ROOT/ninjagrab.sh" -- python "$SCRIPT_DIR/ninjagrab_mcp_server.py"; then
    echo "ninjagrab MCP successfully configured!"
else
    echo "Failed to configure ninjagrab MCP"
    exit 1
fi
echo ""
echo "IMPORTANT: You must restart Claude Code for the new MCP to be available."
echo ""
echo "After restart, you'll have access to the ninjagrab_collect tool:"
echo "- Replaces CLI calls to ninjagrab.sh in plea workflows"
echo "- Concatenates files with delimiters and saves to ninjagrab-out.txt"
echo "- Tool appears as: mcp__ninjagrab__ninjagrab_collect"
echo ""
echo "Example usage in workflows:"
echo "\"Use the ninjagrab MCP to collect these files: file1.py file2.js config.json\""