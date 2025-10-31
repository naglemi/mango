#!/bin/bash

echo "Setting up Grok-4 Proxy MCP Server..."

# Check for API key
if [ -z "$GROK_API_KEY" ]; then
    echo "  GROK_API_KEY environment variable not set"
    echo "Please set it in your ~/.bashrc or environment:"
    echo '  export GROK_API_KEY="your-api-key-here"'
    echo ""
    read -p "Enter your Grok API key now (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        echo "export GROK_API_KEY=\"$api_key\"" >> ~/.bashrc
        export GROK_API_KEY="$api_key"
        echo " API key saved to ~/.bashrc"
    fi
fi

# Create the MCP configuration
cat > /tmp/grok_mcp_config.json << 'EOF'
{
  "mcpServers": {
    "grok-proxy": {
      "command": "python3",
      "args": ["/home/ubuntu/mango/mcp/grok-proxy/grok_proxy_mcp_server.py"],
      "env": {
        "GROK_API_KEY": "${GROK_API_KEY}"
      }
    }
  }
}
EOF

# Merge with existing Claude settings
if [ -f ~/.claude/settings.json ]; then
    echo "Merging with existing Claude settings..."
    python3 -c "
import json
with open('$HOME/.claude/settings.json', 'r') as f:
    settings = json.load(f)
if 'mcpServers' not in settings:
    settings['mcpServers'] = {}
settings['mcpServers']['grok-proxy'] = {
    'command': 'python3',
    'args': ['$HOME/mango/mcp/grok-proxy/grok_proxy_mcp_server.py'],
    'env': {
        'GROK_API_KEY': '\${GROK_API_KEY}'
    }
}
with open('$HOME/.claude/settings.json', 'w') as f:
    json.dump(settings, f, indent=2)
print(' Grok proxy MCP configured in Claude settings')
"
else
    echo "Creating new Claude settings..."
    mkdir -p ~/.claude
    mv /tmp/grok_mcp_config.json ~/.claude/settings.json
fi

echo ""
echo " Grok-4 Proxy MCP setup complete!"
echo ""
echo "IMPORTANT: Restart Claude for changes to take effect"
echo ""
echo "Available tools:"
echo "  - grokplea workflow: /grokplea [issue description]"
echo "  - Direct MCP: mcp__grok-proxy__grok_chat"