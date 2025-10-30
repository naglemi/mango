#!/bin/bash
# Setup EC2 MCP Server for Claude Code

echo "Setting up EC2 MCP server..."

# Install Python dependencies (if needed)
pip3 install --quiet mcp 2>&1 | grep -v "already satisfied" || true

# Create symlink in Claude Code MCP directory
MCP_DIR="$HOME/.config/claude-code/mcps"
mkdir -p "$MCP_DIR"

ln -sf "$PWD/ec2_mcp_server.py" "$MCP_DIR/ec2_mcp_server.py"

echo "✓ EC2 MCP server installed"
echo ""
echo "Available tools:"
echo "  - mcp__ec2__list_instances(state=None)"
echo "  - mcp__ec2__get_instance_logs(instance_id, stream_type='training', tail=100)"
echo "  - mcp__ec2__monitor_instance(instance_id)"
echo "  - mcp__ec2__diagnose_crash(instance_id)"
echo ""
echo "Restart Claude Code to load the MCP server."
