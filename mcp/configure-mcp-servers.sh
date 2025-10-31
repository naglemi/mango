#!/bin/bash
# Configure all MCP servers in Claude's config
# This script is called by setup-claude.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Configuring MCP servers in Claude..."

# Ensure Claude config exists
CONFIG_FILE="$HOME/.claude.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating new Claude config..."
    echo '{}' > "$CONFIG_FILE"
fi

# Python script to add all MCP servers
python3 << EOF
import json
import os
from pathlib import Path

config_file = Path.home() / '.claude.json'
project_root = Path('$PROJECT_ROOT')

# Read existing config
with open(config_file) as f:
    config = json.load(f)

# Initialize mcpServers if not present
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Define all MCP servers
mcp_servers = {
    'train': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/train/train_mcp_server.py')],
        'env': {}
    },
    'pushover': {
        'type': 'stdio',
        'command': 'npx',
        'args': ['-y', 'pushover-mcp', 'start', '--token', 'azottw766yxy7oz3vsu2oz432brx8f', '--user', 'uqek4s2jo8pmrkskp96ravqb85yr15'],
        'env': {}
    },
    'report': {
        'command': 'node',
        'args': [str(project_root / 'mcp/report/index.js')],
        'env': {
            'AWS_ACCESS_KEY_ID': '\${AWS_ACCESS_KEY_ID}',
            'AWS_SECRET_ACCESS_KEY': '\${AWS_SECRET_ACCESS_KEY}',
            'AWS_REGION': '\${AWS_REGION:-us-east-2}',
            'S3_BUCKET_NAME': '\${S3_BUCKET_NAME}',
            'SMTP_SERVER': '\${SMTP_SERVER}',
            'SMTP_PORT': '\${SMTP_PORT:-587}',
            'SMTP_USER': '\${SMTP_USER}',
            'SMTP_PASS': '\${SMTP_PASS}',
            'SMTP_FROM': '\${SMTP_FROM}',
            'SMTP_TO': '\${SMTP_TO}'
        }
    },
    'ninjagrab': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/ninjagrab/ninjagrab_mcp_server.py')],
        'env': {
            'NINJAGRAB_SCRIPT': str(project_root / 'ninjagrab.sh')
        }
    },
    'process-monitor': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/process-monitor/process_monitor_mcp_server.py')],
        'env': {}
    },
    'misalignment-alarm': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/misalignment-alarm/misalignment_alarm_mcp_server.py')],
        'env': {
            'PUSHOVER_APP_TOKEN': '\${PUSHOVER_APP_TOKEN}',
            'PUSHOVER_USER_KEY': '\${PUSHOVER_USER_KEY}'
        }
    },
    'o3-proxy': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/o3-proxy/o3_proxy_mcp_server.py')],
        'env': {
            'OPENAI_API_KEY': '\${OPENAI_API_KEY}'
        }
    },
    'deepseek-proxy': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/deepseek-proxy/deepseek_proxy_mcp_server.py')],
        'env': {
            'AWS_ACCESS_KEY_ID': '\${AWS_ACCESS_KEY_ID}',
            'AWS_SECRET_ACCESS_KEY': '\${AWS_SECRET_ACCESS_KEY}',
            'AWS_REGION': '\${AWS_REGION:-us-east-2}'
        }
    },
    'grok-proxy': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/grok-proxy/grok_proxy_mcp_server.py')],
        'env': {
            'GROK_API_KEY': '\${GROK_API_KEY}'
        }
    },
    'pushover-notify': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/pushover-notify/pushover_notify_mcp_server.py')],
        'env': {
            'PUSHOVER_APP_TOKEN': '\${PUSHOVER_APP_TOKEN}',
            'PUSHOVER_USER_KEY': '\${PUSHOVER_USER_KEY}'
        }
    },
    'time-estimator': {
        'command': 'estimate-mcp',
        'args': [],
        'env': {}
    },
    'sleep': {
        'command': 'python3',
        'args': [str(project_root / 'mcp/sleep/sleep_mcp_server.py')],
        'env': {}
    }
}

# Check for mango-dev and add its MCP servers
mango_dev = Path.home() / 'mango-dev'
if mango_dev.exists():
    print("  Detected ~/mango-dev - adding development MCP servers...")

    # Expanse MCP
    expanse_server = mango_dev / 'mcp_servers/expanse/server.py'
    if expanse_server.exists():
        mcp_servers['expanse'] = {
            'command': 'python3',
            'args': [str(expanse_server)],
            'env': {}
        }
        print("    Found Expanse MCP")

# Add/update MCP servers
for name, server_config in mcp_servers.items():
    # Skip file checking for npm-based servers
    if server_config['command'] in ['npx', 'node']:
        config['mcpServers'][name] = server_config
        print(f"   Configured {name}")
    else:
        # Check if the server file exists for Python servers
        server_file = server_config['args'][0]
        if Path(server_file).exists():
            config['mcpServers'][name] = server_config
            print(f"   Configured {name}")
        else:
            print(f"   Skipping {name} (server not found: {server_file})")

# Write updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f" MCP servers configured in {config_file}")
EOF

echo ""
echo "MCP server configuration complete!"
echo "Restart Claude for changes to take effect."