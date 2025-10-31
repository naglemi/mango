#!/bin/bash

# Pushover MCP Setup Script for AI Coding Assistants
# Sets up the pushover-mcp server for all supported AI assistants

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}$1${NC}"; }
print_warning() { echo -e "${YELLOW}$1${NC}"; }
print_error() { echo -e "${RED}$1${NC}"; }
print_info() { echo -e "${BLUE}$1${NC}"; }

echo "Pushover MCP Setup for AI Assistants"
echo "======================================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install Node.js/npm first."
    exit 1
fi

# Install pushover-mcp globally if not already installed
print_info "Checking pushover-mcp installation..."
if ! npm list -g pushover-mcp &> /dev/null; then
    print_info "Installing pushover-mcp globally..."
    npm install -g pushover-mcp
    print_success "pushover-mcp installed successfully"
else
    print_success "pushover-mcp is already installed"
fi

# Get Pushover credentials
echo ""
echo "Enter your Pushover credentials (or press Enter to use defaults from the Python script):"
read -p "Pushover App Token [azottw766yxy7oz3vsu2oz432brx8f]: " APP_TOKEN
APP_TOKEN=${APP_TOKEN:-azottw766yxy7oz3vsu2oz432brx8f}

read -p "Pushover User Key [uqek4s2jo8pmrkskp96ravqb85yr15]: " USER_KEY
USER_KEY=${USER_KEY:-uqek4s2jo8pmrkskp96ravqb85yr15}

# 1. Claude Code - .mcp.json in project root
echo ""
echo "Setting up Pushover MCP for Claude Code..."

# Create .mcp.json for Claude Code
cat > "$(pwd)/.mcp.json" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
print_success "Created .mcp.json for Claude Code"
print_warning "You'll need to approve this server when Claude Code first tries to use it"

# 2. Claude Desktop - ~/Library/Application Support/Claude/claude_desktop_config.json
echo ""
echo "Setting up Pushover MCP for Claude Desktop..."

CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CLAUDE_DESKTOP_DIR="$HOME/Library/Application Support/Claude"

# Create directory if it doesn't exist
mkdir -p "$CLAUDE_DESKTOP_DIR"

# Check if config exists and has content
if [ -f "$CLAUDE_DESKTOP_CONFIG" ] && [ -s "$CLAUDE_DESKTOP_CONFIG" ]; then
    # Backup existing config
    cp "$CLAUDE_DESKTOP_CONFIG" "$CLAUDE_DESKTOP_CONFIG.backup"
    print_info "Backed up existing Claude Desktop config"
    
    # Use Python to merge configurations
    python3 -c "
import json
import sys

config_path = '$CLAUDE_DESKTOP_CONFIG'

# Read existing config
with open(config_path, 'r') as f:
    config = json.load(f)

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add pushover server
config['mcpServers']['pushover'] = {
    'command': 'npx',
    'args': ['-y', 'pushover-mcp'],
    'env': {
        'PUSHOVER_APP_TOKEN': '$APP_TOKEN',
        'PUSHOVER_USER_KEY': '$USER_KEY'
    }
}

# Write updated config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"
    print_success "Updated Claude Desktop configuration"
else
    # Create new config
    cat > "$CLAUDE_DESKTOP_CONFIG" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
    print_success "Created Claude Desktop configuration"
fi
print_warning "Restart Claude Desktop for changes to take effect"

# 3. Cursor - .cursor/mcp.json
echo ""
echo "Setting up Pushover MCP for Cursor..."

mkdir -p "$(pwd)/.cursor"
cat > "$(pwd)/.cursor/mcp.json" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
print_success "Created .cursor/mcp.json for Cursor"

# 4. Windsurf - ~/.codeium/windsurf/mcp_config.json
echo ""
echo "Setting up Pushover MCP for Windsurf..."

WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
WINDSURF_DIR="$HOME/.codeium/windsurf"

mkdir -p "$WINDSURF_DIR"

# Check if config exists
if [ -f "$WINDSURF_CONFIG" ] && [ -s "$WINDSURF_CONFIG" ]; then
    cp "$WINDSURF_CONFIG" "$WINDSURF_CONFIG.backup"
    print_info "Backed up existing Windsurf config"
    
    # Use Python to merge
    python3 -c "
import json

config_path = '$WINDSURF_CONFIG'

with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['pushover'] = {
    'command': 'npx',
    'args': ['-y', 'pushover-mcp'],
    'env': {
        'PUSHOVER_APP_TOKEN': '$APP_TOKEN',
        'PUSHOVER_USER_KEY': '$USER_KEY'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"
    print_success "Updated Windsurf configuration"
else
    cat > "$WINDSURF_CONFIG" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
    print_success "Created Windsurf configuration"
fi
print_warning "Press the refresh button in Windsurf MCP settings after setup"

# 5. Roo Code - cline_mcp_settings.json (global) and .roo/mcp.json (project)
echo ""
echo "Setting up Pushover MCP for Roo Code..."

# Find VS Code settings directory
if [ -d "$HOME/Library/Application Support/Code/User" ]; then
    VSCODE_USER_DIR="$HOME/Library/Application Support/Code/User"
elif [ -d "$HOME/.config/Code/User" ]; then
    VSCODE_USER_DIR="$HOME/.config/Code/User"
else
    print_warning "Could not find VS Code user directory for global Roo Code settings"
    VSCODE_USER_DIR=""
fi

# Set up global config if VS Code directory found
if [ ! -z "$VSCODE_USER_DIR" ]; then
    ROO_GLOBAL_CONFIG="$VSCODE_USER_DIR/cline_mcp_settings.json"
    
    if [ -f "$ROO_GLOBAL_CONFIG" ] && [ -s "$ROO_GLOBAL_CONFIG" ]; then
        cp "$ROO_GLOBAL_CONFIG" "$ROO_GLOBAL_CONFIG.backup"
        print_info "Backed up existing Roo Code global config"
        
        python3 -c "
import json

config_path = '$ROO_GLOBAL_CONFIG'

with open(config_path, 'r') as f:
    config = json.load(f)

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['pushover'] = {
    'command': 'npx',
    'args': ['-y', 'pushover-mcp'],
    'env': {
        'PUSHOVER_APP_TOKEN': '$APP_TOKEN',
        'PUSHOVER_USER_KEY': '$USER_KEY'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"
        print_success "Updated Roo Code global configuration"
    else
        cat > "$ROO_GLOBAL_CONFIG" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
        print_success "Created Roo Code global configuration"
    fi
fi

# Set up project-specific config
mkdir -p "$(pwd)/.roo"
cat > "$(pwd)/.roo/mcp.json" << EOF
{
  "mcpServers": {
    "pushover": {
      "command": "npx",
      "args": ["-y", "pushover-mcp"],
      "env": {
        "PUSHOVER_APP_TOKEN": "$APP_TOKEN",
        "PUSHOVER_USER_KEY": "$USER_KEY"
      }
    }
  }
}
EOF
print_success "Created .roo/mcp.json for Roo Code (project-specific)"

# 6. OpenAI Codex - Note about MCP support
echo ""
echo "OpenAI Codex MCP Support..."
print_warning "OpenAI Codex has limited MCP support through community implementations"
print_info "You may need to use the Python script directly or wait for official MCP support"

# Summary
echo ""
echo "======================================="
echo "Pushover MCP Setup Complete!"
echo ""
echo "Configurations created:"
echo "  • Claude Code: .mcp.json (project)"
echo "  • Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "  • Cursor: .cursor/mcp.json (project)"
echo "  • Windsurf: ~/.codeium/windsurf/mcp_config.json (global)"
echo "  • Roo Code: cline_mcp_settings.json (global) & .roo/mcp.json (project)"
echo ""
echo "Available MCP Tools:"
echo "  • send_notification - Send a push notification via Pushover"
echo ""
echo "Usage example in AI assistants:"
echo '  "Send a notification saying Build completed successfully"'
echo ""
echo "Notes:"
echo "  • Some assistants may require approval on first use"
echo "  • Restart Claude Desktop to apply changes"
echo "  • Refresh MCP settings in Windsurf"
echo "  • Project-specific configs should be added to .gitignore"