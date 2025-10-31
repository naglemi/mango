#!/bin/bash

# Pushover Notification Script
# Provides similar functionality to the Python script but for manual use
# The MCP integration allows AI assistants to send notifications directly

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Require credentials from environment
APP_TOKEN="${PUSHOVER_APP_TOKEN}"
USER_KEY="${PUSHOVER_USER_KEY}"

if [ -z "$APP_TOKEN" ] || [ -z "$USER_KEY" ]; then
    echo -e "${RED}Error: Pushover credentials not found${NC}"
    echo "Please set PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY environment variables"
    echo "Run the setup script to configure: mcp/pushover/setup-pushover-mcp.sh"
    exit 1
fi

# Parse command line arguments
PAGE=false
CUSTOM_SOUND=""
MESSAGE=""
TITLE=""
IS_MARKDOWN=false

usage() {
    echo "Usage: $0 [options] <message|markdown_file>"
    echo ""
    echo "Options:"
    echo "  -t, --title <title>     Set notification title"
    echo "  -p, --page              Use question sounds (for paging)"
    echo "  -s, --sound <sound>     Use specific sound"
    echo "  -m, --markdown          Treat message as markdown file path"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 'Build completed successfully'"
    echo "  $0 -t 'Build Status' 'All tests passed'"
    echo "  $0 -m -t 'Ninja Report' ./scrolls/analysis.md"
    echo "  $0 --page -t 'Need Input' 'Should I proceed with deployment?'"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -p|--page)
            PAGE=true
            shift
            ;;
        -s|--sound)
            CUSTOM_SOUND="$2"
            shift 2
            ;;
        -m|--markdown)
            IS_MARKDOWN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            MESSAGE="$1"
            shift
            ;;
    esac
done

if [ -z "$MESSAGE" ]; then
    echo "Error: Message or file path required"
    usage
fi

# Determine sound
if [ ! -z "$CUSTOM_SOUND" ]; then
    SOUND="$CUSTOM_SOUND"
elif [ "$PAGE" = true ]; then
    SOUND="question$((RANDOM % 9 + 1))"
else
    SOUND="plan$((RANDOM % 9 + 1))"
fi

# Function to send notification
send_notification() {
    local msg="$1"
    local title="$2"
    local sound="$3"
    
    response=$(curl -s -X POST "https://api.pushover.net/1/messages.json" \
        -F "token=$APP_TOKEN" \
        -F "user=$USER_KEY" \
        -F "message=$msg" \
        -F "title=$title" \
        -F "sound=$sound" \
        -F "html=1")
    
    if echo "$response" | grep -q '"status":1'; then
        echo -e "${GREEN} Notification sent successfully${NC}"
        return 0
    else
        echo -e "${RED} Failed to send notification${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Process markdown if needed
if [ "$IS_MARKDOWN" = true ]; then
    if [ ! -f "$MESSAGE" ]; then
        echo -e "${RED} Markdown file not found: $MESSAGE${NC}"
        exit 1
    fi
    
    # Check if pandoc is available for better markdown conversion
    if command -v pandoc &> /dev/null; then
        HTML_CONTENT=$(pandoc -f markdown -t html "$MESSAGE" 2>/dev/null | \
            sed 's/<h1>/<b>/g; s/<\/h1>/<\/b><br><br>/g' | \
            sed 's/<h2>/<b>/g; s/<\/h2>/<\/b><br><br>/g' | \
            sed 's/<li>/• /g; s/<\/li>/<br>/g' | \
            sed 's/<ul>/<br>/g; s/<\/ul>/<br>/g' | \
            sed 's/<pre>//g; s/<\/pre>//g' | \
            sed 's/<p>//g; s/<\/p>/<br><br>/g')
    else
        # Fallback to basic conversion
        HTML_CONTENT=$(cat "$MESSAGE" | \
            sed 's/^# \(.*\)$/<b>\1<\/b><br><br>/g' | \
            sed 's/^## \(.*\)$/<b>\1<\/b><br><br>/g' | \
            sed 's/\*\*\([^*]*\)\*\*/<b>\1<\/b>/g' | \
            sed 's/\*\([^*]*\)\*/<i>\1<\/i>/g' | \
            sed 's/^- /• /g' | \
            sed 's/`\([^`]*\)`/<i>\1<\/i>/g' | \
            sed 's/$//')
    fi
    
    send_notification "$HTML_CONTENT" "$TITLE" "$SOUND"
else
    send_notification "$MESSAGE" "$TITLE" "$SOUND"
fi

# Log to pushover.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sent notification: ${TITLE:-No title} - Sound: $SOUND" >> pushover.log