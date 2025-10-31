#!/bin/bash

# Setup Report MCP Server for S3-based reports with email notifications

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

echo "Report MCP Server Setup"
echo "========================="
echo ""
echo "This MCP server enables AI assistants to:"
echo "  • Upload report files/images to S3"
echo "  • Send email notifications with links"
echo "  • List and retrieve past reports"
echo ""

# Check for npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install Node.js/npm first."
    exit 1
fi

# Get configuration
echo "Please provide AWS configuration:"
echo ""

# Check if this is Michael Nagle's setup
if [[ "$USER" == "michaelnagle" ]] || [[ "$USER" == "mnagle" ]]; then
    print_info "Detected Michael Nagle's account - using existing infrastructure"
    echo ""
fi

# S3 Bucket
read -p "S3 Bucket name for reports [usability-reports]: " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-usability-reports}

# AWS Region
read -p "AWS Region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

# Email configuration
echo ""
echo "Email configuration (using AWS SES):"

# Set defaults for Michael Nagle
DEFAULT_EMAIL=""
if [[ "$USER" == "michaelnagle" ]] || [[ "$USER" == "mnagle" ]]; then
    DEFAULT_EMAIL="slurmalerts1017@gmail.com"
fi

read -p "From email address${DEFAULT_EMAIL:+ [$DEFAULT_EMAIL]}: " EMAIL_FROM
EMAIL_FROM=${EMAIL_FROM:-$DEFAULT_EMAIL}
if [ -z "$EMAIL_FROM" ]; then
    print_error "From email is required"
    exit 1
fi

read -p "To email address${DEFAULT_EMAIL:+ [$DEFAULT_EMAIL]}: " EMAIL_TO
EMAIL_TO=${EMAIL_TO:-$DEFAULT_EMAIL}
if [ -z "$EMAIL_TO" ]; then
    print_error "To email is required"
    exit 1
fi

# URL expiration
read -p "Pre-signed URL expiration in seconds [604800 (7 days)]: " URL_EXPIRATION
URL_EXPIRATION=${URL_EXPIRATION:-604800}

# Install the MCP server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_info "Installing dependencies..."
cd "$SCRIPT_DIR"
npm install

print_success "Report MCP server installed"

# Environment variables will be passed through .mcp.json

print_success "Created configuration file"

# Update MCP configurations for each platform

# 1. Claude Code - .mcp.json
echo ""
print_info "Updating Claude Code configuration..."
MCP_CONFIG="$PROJECT_ROOT/.mcp.json"

if [ -f "$MCP_CONFIG" ]; then
    # Backup and update existing
    cp "$MCP_CONFIG" "$MCP_CONFIG.backup"
    
    # Use Python to merge
    python3 -c "
import json
config_path = '.mcp.json'
with open(config_path, 'r') as f:
    config = json.load(f)
if 'mcpServers' not in config:
    config['mcpServers'] = {}
config['mcpServers']['report'] = {
    'command': 'node',
    'args': ['$SCRIPT_DIR/index.js'],
    'env': {
        'REPORT_BUCKET': '$BUCKET_NAME',
        'AWS_REGION': '$AWS_REGION',
        'REPORT_EMAIL_FROM': '$EMAIL_FROM',
        'REPORT_EMAIL_TO': '$EMAIL_TO',
        'REPORT_URL_EXPIRATION': '$URL_EXPIRATION'
    }
}
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"
else
    # Create new
    cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "report": {
      "command": "node",
      "args": ["$SCRIPT_DIR/index.js"],
      "env": {
        "REPORT_BUCKET": "$BUCKET_NAME",
        "AWS_REGION": "$AWS_REGION",
        "REPORT_EMAIL_FROM": "$EMAIL_FROM",
        "REPORT_EMAIL_TO": "$EMAIL_TO",
        "REPORT_URL_EXPIRATION": "$URL_EXPIRATION"
      }
    }
  }
}
EOF
fi
print_success "Updated Claude Code configuration"

# Similar updates for other platforms...
print_info "Add similar configuration to other AI assistants as needed"

echo ""
echo "================================="
echo " Report MCP Server Setup Complete!"
echo ""
echo "Available MCP Tools:"
echo "  • send_report - Send a report with text and file attachments"
echo "  • list_reports - List recent reports from S3"
echo ""
echo "Usage example in AI assistants:"
echo '  "Send a report titled Test Results with the content All tests passed and attach ./results.png"'
echo ""
if [[ "$USER" == "michaelnagle" ]] || [[ "$USER" == "mnagle" ]]; then
    echo " Using your existing AWS infrastructure:"
    echo "  • S3 bucket: $BUCKET_NAME (already exists)"
    echo "  • Email: $EMAIL_FROM (already verified in SES)"
    echo "  • AWS credentials from your shell config"
else
    echo "Important AWS Setup Required:"
    echo "  1. Create S3 bucket: $BUCKET_NAME"
    echo "  2. Verify email in SES: $EMAIL_FROM"
    echo "  3. Ensure AWS credentials are configured"
fi
echo ""
echo "Reports will be organized in S3 as:"
echo "  $BUCKET_NAME/<agent_name>/<date>_<time>/<files>"
echo ""
print_info "Restart Claude Code to load the new MCP configuration"
echo ""
echo "After restart, test by asking Claude:"
echo '  "Send me a test report with the message Hello World"'