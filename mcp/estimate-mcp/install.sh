#!/bin/bash
# Installation script for estimate-mcp MCP server

set -e

echo "Installing estimate-mcp MCP server..."

# Install the package
pip install -e .

echo ""
echo "Installation complete!"
echo ""
echo "MCP server command: estimate-mcp"
echo "Location: $(which estimate-mcp)"
echo ""
echo "To integrate with Claude Desktop, add this to your config:"
echo ""
echo '{
  "mcpServers": {
    "estimate": {
      "command": "'$(which estimate-mcp)'"
    }
  }
}'
echo ""
