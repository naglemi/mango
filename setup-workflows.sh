#!/bin/bash

# Setup Claude Code workflows and MCP servers

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Base directory where this script lives
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="$BASE_DIR/workflows"

# Parse command line arguments
DEVELOPER_MODE=0
SHOW_HELP=0
UNINSTALL=0

for arg in "$@"; do
    case $arg in
        --developer)
            DEVELOPER_MODE=1
            shift
            ;;
        --help|-h)
            SHOW_HELP=1
            shift
            ;;
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        *)
            ;;
    esac
done

if [ $SHOW_HELP -eq 1 ]; then
    echo "Usage: ./setup-workflows.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --developer    Install private workflows and MCPs (developer mode)"
    echo "  --uninstall    Remove all workflows and MCPs"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Default: Interactive selection of workflows and MCPs"
    exit 0
fi

# Uninstall mode
if [ $UNINSTALL -eq 1 ]; then
    echo -e "${BLUE}Uninstalling workflows and MCPs${NC}"
    echo ""

    # Load configuration to see what was installed
    CONFIG_FILE="$WORKFLOWS_DIR/workflows-installed.json"
    if [ -f "$CONFIG_FILE" ]; then
        echo "Reading installation record..."

        # Remove workflows
        WORKFLOW_IDS=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(' '.join(config.get('workflows', [])))")
        if [ -n "$WORKFLOW_IDS" ]; then
            echo -e "${BLUE}Removing workflows...${NC}"
            for wf in $WORKFLOW_IDS; do
                rm -f ~/.claude/commands/${wf}.md
                echo "  Removed $wf"
            done
        fi

        # Remove MCPs
        MCP_IDS=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(' '.join(config.get('mcps', [])))")
        if [ -n "$MCP_IDS" ]; then
            echo -e "${BLUE}Removing MCPs...${NC}"
            for mcp in $MCP_IDS; do
                claude mcp remove $mcp --scope user 2>/dev/null || true
                echo "  Removed $mcp"
            done
        fi

        # Remove configuration file
        rm -f "$CONFIG_FILE"
        echo ""
        echo -e "${GREEN}Uninstallation complete!${NC}"
    else
        echo -e "${YELLOW}No installation record found${NC}"
        echo "Nothing to uninstall"
    fi

    exit 0
fi

# Check if Claude Code is installed first
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code is not installed"
    echo "The 'claude' command was not found in PATH"
    exit 1
fi

echo -e "${BLUE}Setting up Claude Code Workflows and MCPs${NC}"
echo ""

# Check for required commands
echo -e "${BLUE}Checking required commands...${NC}"
MISSING_COMMANDS=()
CRITICAL_SETUP_NEEDED=()

# Check fzf
if ! command -v fzf &> /dev/null; then
    echo -e "  ${RED}${NC} fzf NOT FOUND"
    MISSING_COMMANDS+=("fzf")
else
    echo -e "  ${GREEN}[OK]${NC} fzf found"
fi

# Check npm/node/claude/gh
for cmd in npm node claude gh; do
    if command -v $cmd &> /dev/null; then
        echo -e "  ${GREEN}[OK]${NC} $cmd found"
    else
        echo -e "  ${RED}${NC} $cmd NOT FOUND"
        MISSING_COMMANDS+=($cmd)
    fi
done

# Check python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "  ${GREEN}[OK]${NC} python3 found"
elif command -v python &> /dev/null; then
    if python -c "import sys; exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
        PYTHON_CMD="python"
        echo -e "  ${GREEN}[OK]${NC} python found (Python 3)"
    else
        echo -e "  ${RED}${NC} python found but it's Python 2"
        MISSING_COMMANDS+=("python3")
    fi
else
    echo -e "  ${RED}${NC} python/python3 NOT FOUND"
    MISSING_COMMANDS+=("python3")
fi

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Missing required commands: ${MISSING_COMMANDS[*]}${NC}"
    echo ""
    echo "Please install:"
    for cmd in "${MISSING_COMMANDS[@]}"; do
        case $cmd in
            npm|node)
                echo "  - Node.js and npm: https://nodejs.org/"
                echo "    macOS: brew install node"
                echo "    Ubuntu/Debian: sudo apt install nodejs npm"
                ;;
            claude)
                echo "  - Claude Code: Follow instructions at https://claude.ai/download"
                ;;
            python3)
                echo "  - Python 3: https://www.python.org/downloads/"
                echo "    macOS: brew install python3"
                echo "    Ubuntu/Debian: sudo apt install python3"
                ;;
            fzf)
                echo "  - fzf: https://github.com/junegunn/fzf"
                echo "    macOS: brew install fzf"
                echo "    Ubuntu/Debian: sudo apt install fzf"
                ;;
            gh)
                echo "  - GitHub CLI: https://cli.github.com/"
                echo "    macOS: brew install gh"
                echo "    Ubuntu/Debian: sudo apt install gh"
                ;;
        esac
    done
    exit 1
fi
echo ""

# Check GitHub authentication (CRITICAL for discuss workflow)
echo -e "${BLUE}Checking GitHub authentication...${NC}"
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null; then
        GH_USER=$(gh auth status 2>&1 | grep "Logged in" | sed 's/.*as \([^ ]*\).*/\1/')
        echo -e "  ${GREEN}[OK]${NC} Authenticated as ${GH_USER}"
    else
        echo -e "  ${RED}${NC} GitHub CLI not authenticated"
        echo ""
        echo -e "${YELLOW}CRITICAL: The 'discuss' workflow requires GitHub authentication${NC}"
        echo ""
        echo "The discuss workflow is the MOST IMPORTANT feature in this toolkit."
        echo "It enables multi-agent collaboration via GitHub issue threads."
        echo ""
        echo "To authenticate, run:"
        echo "  gh auth login"
        echo ""
        read -p "Continue without GitHub auth? (workflows will be installed but /discuss won't work) [y/N]: " -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup cancelled. Please run 'gh auth login' and try again."
            exit 1
        fi
        CRITICAL_SETUP_NEEDED+=("GitHub authentication for discuss workflow")
    fi
fi
echo ""

# Configure blog settings before workflow selection
echo -e "${BLUE}╭─────────────────────────────────────────────────────────╮${NC}"
echo -e "${BLUE}│           BLOG & REPORT CONFIGURATION                │${NC}"
echo -e "${BLUE}╰─────────────────────────────────────────────────────────╯${NC}"
echo ""

# Check if blog configuration already exists in bashrc
EXISTING_BLOG_MODE=""
EXISTING_BLOG_PATH=""
EXISTING_NOTEBOOKS_DIR=""
EXISTING_REPORTS_DIR=""

if [ -f ~/.bashrc ]; then
    # Extract existing blog configuration from bashrc
    EXISTING_BLOG_MODE=$(grep "^export BLOG_MODE=" ~/.bashrc | tail -1 | sed 's/export BLOG_MODE="\(.*\)"/\1/')
    EXISTING_BLOG_PATH=$(grep "^export BLOG_PATH=" ~/.bashrc | tail -1 | sed 's/export BLOG_PATH="\(.*\)"/\1/')
    EXISTING_NOTEBOOKS_DIR=$(grep "^export BLOG_NOTEBOOKS_DIR=" ~/.bashrc | tail -1 | sed 's/export BLOG_NOTEBOOKS_DIR="\(.*\)"/\1/')
    EXISTING_REPORTS_DIR=$(grep "^export BLOG_REPORTS_DIR=" ~/.bashrc | tail -1 | sed 's/export BLOG_REPORTS_DIR="\(.*\)"/\1/')
fi

# If existing configuration found, offer to keep it
if [ -n "$EXISTING_BLOG_MODE" ] && [ "$EXISTING_BLOG_MODE" != "SKIP" ]; then
    echo -e "${GREEN}Existing blog configuration found:${NC}"
    echo "  Mode: $EXISTING_BLOG_MODE"
    echo "  Path: $EXISTING_BLOG_PATH"
    if [ "$EXISTING_BLOG_MODE" = "REPO" ]; then
        echo "  Notebooks: $EXISTING_BLOG_PATH/$EXISTING_NOTEBOOKS_DIR"
        echo "  Reports: $EXISTING_BLOG_PATH/$EXISTING_REPORTS_DIR"
    fi
    echo ""
    echo "Options:"
    echo "  [1] Keep existing configuration"
    echo "  [2] Reconfigure"
    echo "  [3] Skip"
    echo ""
    read -p "Choice [1/2/3]: " -r BLOG_CONFIG_CHOICE
    echo

    if [ "$BLOG_CONFIG_CHOICE" = "1" ]; then
        echo -e "${GREEN}Keeping existing blog configuration${NC}"
        # Create temp file with existing config
        cat > "$WORKFLOWS_DIR/.blog-config.tmp" << EOF
BLOG_MODE="$EXISTING_BLOG_MODE"
BLOG_PATH="$EXISTING_BLOG_PATH"
NOTEBOOKS_DIR="$EXISTING_NOTEBOOKS_DIR"
REPORTS_DIR="$EXISTING_REPORTS_DIR"
EOF
    elif [ "$BLOG_CONFIG_CHOICE" = "3" ]; then
        echo -e "${YELLOW}Skipping blog configuration${NC}"
    else
        # Reconfigure - fall through to normal configuration
        BLOG_CONFIG_CHOICE="2"
    fi
else
    # No existing config, show intro and ask
    echo "The 'blog' workflow can work in two modes:"
    echo ""
    echo "  1. REPO MODE   - Integrates with your blog repository"
    echo "                   (saves to _notebooks/ and _reports/)"
    echo ""
    echo "  2. FOLDER MODE - Saves notebooks/reports to a local folder"
    echo "                   (no git integration)"
    echo ""
    echo -e "${YELLOW}Note: You can configure or change this later in Settings (Ctrl+G → w)${NC}"
    echo ""
    read -p "Configure blog settings now? [Y/n]: " -r
    echo

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        BLOG_CONFIG_CHOICE="3"  # Skip
    else
        BLOG_CONFIG_CHOICE="2"  # Configure
    fi
fi

if [ "$BLOG_CONFIG_CHOICE" = "2" ]; then
    # Ask for blog mode
    echo "Select blog mode:"
    echo "  [1] REPO MODE   - I have a blog repository"
    echo "  [2] FOLDER MODE - Save to local folder only"
    echo "  [3] SKIP        - Configure later"
    echo ""
    read -p "Choice [1/2/3]: " -r BLOG_MODE_CHOICE
    echo

    BLOG_MODE="SKIP"
    BLOG_PATH=""
    NOTEBOOKS_DIR="_notebooks"
    REPORTS_DIR="_reports"

    case "$BLOG_MODE_CHOICE" in
        1)
            BLOG_MODE="REPO"
            echo -e "${BLUE}Enter path to your blog repository:${NC}"
            read -p "Path (e.g., ~/blog): " -r BLOG_PATH_INPUT

            # Expand ~ to home directory
            BLOG_PATH="${BLOG_PATH_INPUT/#\~/$HOME}"

            # Check if directory exists
            if [ ! -d "$BLOG_PATH" ]; then
                echo -e "${YELLOW}Directory does not exist: $BLOG_PATH${NC}"
                read -p "Create it? [y/N]: " -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    mkdir -p "$BLOG_PATH"
                    echo -e "${GREEN}Created directory${NC}"
                else
                    echo -e "${YELLOW}Skipping blog configuration${NC}"
                    BLOG_MODE="SKIP"
                fi
            fi

            if [ "$BLOG_MODE" = "REPO" ]; then
                # Ask about subdirectories
                echo ""
                echo -e "${BLUE}Configure subdirectories (press Enter to use defaults):${NC}"
                echo ""
                read -p "Notebooks directory [_notebooks]: " -r NOTEBOOKS_INPUT
                read -p "Reports directory [_reports]: " -r REPORTS_INPUT

                [ -n "$NOTEBOOKS_INPUT" ] && NOTEBOOKS_DIR="$NOTEBOOKS_INPUT"
                [ -n "$REPORTS_INPUT" ] && REPORTS_DIR="$REPORTS_INPUT"

                echo ""
                echo -e "${GREEN}Blog configuration:${NC}"
                echo "  Mode: REPO"
                echo "  Path: $BLOG_PATH"
                echo "  Notebooks: $BLOG_PATH/$NOTEBOOKS_DIR"
                echo "  Reports: $BLOG_PATH/$REPORTS_DIR"
            fi
            ;;
        2)
            BLOG_MODE="FOLDER"
            echo -e "${BLUE}Enter path for blog outputs:${NC}"
            read -p "Path (e.g., ~/blog-outputs): " -r BLOG_PATH_INPUT

            # Expand ~ to home directory
            BLOG_PATH="${BLOG_PATH_INPUT/#\~/$HOME}"

            # Check if directory exists
            if [ ! -d "$BLOG_PATH" ]; then
                echo -e "${YELLOW}Directory does not exist: $BLOG_PATH${NC}"
                read -p "Create it? [y/N]: " -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    mkdir -p "$BLOG_PATH"
                    echo -e "${GREEN}Created directory${NC}"
                else
                    echo -e "${YELLOW}Skipping blog configuration${NC}"
                    BLOG_MODE="SKIP"
                fi
            fi

            if [ "$BLOG_MODE" = "FOLDER" ]; then
                echo ""
                echo -e "${GREEN}Blog configuration:${NC}"
                echo "  Mode: FOLDER"
                echo "  Path: $BLOG_PATH"
            fi
            ;;
        3|*)
            echo -e "${YELLOW}Skipping blog configuration${NC}"
            echo "You can configure this later in Settings (Ctrl+G → w)"
            ;;
    esac

    # Save blog configuration to temporary file for later use
    if [ "$BLOG_MODE" != "SKIP" ]; then
        cat > "$WORKFLOWS_DIR/.blog-config.tmp" << EOF
BLOG_MODE="$BLOG_MODE"
BLOG_PATH="$BLOG_PATH"
NOTEBOOKS_DIR="$NOTEBOOKS_DIR"
REPORTS_DIR="$REPORTS_DIR"
EOF
    fi
fi

echo ""

# Configure workflows and MCPs interactively
chmod +x "$WORKFLOWS_DIR/configure-workflows.py"
chmod +x "$WORKFLOWS_DIR/install-workflows.py"

if [ $DEVELOPER_MODE -eq 1 ]; then
    echo "Developer mode: Selecting all workflows and MCPs by default"
    python3 "$WORKFLOWS_DIR/configure-workflows.py" --developer
else
    echo "Interactive workflow and MCP selection..."
    echo ""
    python3 "$WORKFLOWS_DIR/configure-workflows.py"
fi

# Check if configuration was successful
if [ ! -f "$WORKFLOWS_DIR/workflows-installed.json" ]; then
    echo ""
    echo "Configuration was cancelled or failed"
    echo "Run this script again to configure workflows and MCPs"
    exit 0
fi

# Check environment variables for selected MCPs and workflows (skip in developer mode)
if [ $DEVELOPER_MODE -eq 0 ]; then
    echo ""
    echo -e "${BLUE}Checking environment variables for selected items...${NC}"
    chmod +x "$WORKFLOWS_DIR/check-envars.py"

    # Get selected MCPs and workflows from config
    SELECTED_MCPS=$(python3 -c "import json; config=json.load(open('$WORKFLOWS_DIR/workflows-installed.json')); print(' '.join(config.get('mcps', [])))")
    SELECTED_WORKFLOWS=$(python3 -c "import json; config=json.load(open('$WORKFLOWS_DIR/workflows-installed.json')); print(' '.join(config.get('workflows', [])))")

    # Build command with both MCPs and workflows
    CHECK_CMD="python3 \"$WORKFLOWS_DIR/check-envars.py\""
    if [ -n "$SELECTED_MCPS" ]; then
        CHECK_CMD="$CHECK_CMD --mcps $SELECTED_MCPS"
    fi
    if [ -n "$SELECTED_WORKFLOWS" ]; then
        CHECK_CMD="$CHECK_CMD --workflows $SELECTED_WORKFLOWS"
    fi

    # Run checker if we have anything to check
    if [ -n "$SELECTED_MCPS" ] || [ -n "$SELECTED_WORKFLOWS" ]; then
        # Run interactively and save output to temp file
        ENVAR_TMPFILE=$(mktemp)
        eval $CHECK_CMD | tee "$ENVAR_TMPFILE"

        # Extract valid items from output
        VALID_MCPS=$(grep "VALID_MCPS=" "$ENVAR_TMPFILE" | sed 's/VALID_MCPS=//')
        VALID_WORKFLOWS=$(grep "VALID_WORKFLOWS=" "$ENVAR_TMPFILE" | sed 's/VALID_WORKFLOWS=//')
        rm -f "$ENVAR_TMPFILE"

        # Update configuration with only valid items
        export UPDATE_VALID_MCPS="$VALID_MCPS"
        export UPDATE_VALID_WORKFLOWS="$VALID_WORKFLOWS"
        export WORKFLOWS_DIR="$WORKFLOWS_DIR"
        python3 << 'EOF'
import json
import os
from pathlib import Path

config_file = Path(os.environ["WORKFLOWS_DIR"]) / "workflows-installed.json"
with open(config_file, 'r') as f:
    config = json.load(f)

# Update MCPs if we checked them
valid_mcps_str = os.environ.get("UPDATE_VALID_MCPS", "")
if valid_mcps_str:
    valid_mcps = json.loads(valid_mcps_str)
    config['mcps'] = valid_mcps

# Update workflows if we checked them
valid_workflows_str = os.environ.get("UPDATE_VALID_WORKFLOWS", "")
if valid_workflows_str:
    valid_workflows = json.loads(valid_workflows_str)
    config['workflows'] = valid_workflows

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
EOF
        # Reload bashrc to pick up any newly added environment variables
        if [ -f ~/.bashrc ]; then
            source ~/.bashrc
        fi
        echo ""
        echo -e "${GREEN}[OK]${NC} Environment variable check complete"
    fi
fi

# Install npm dependencies for Report MCP if selected
if grep -q '"report"' "$WORKFLOWS_DIR/workflows-installed.json"; then
    echo ""
    echo -e "${BLUE}Installing Report MCP dependencies...${NC}"
    if [ -d "$BASE_DIR/mcp/report" ]; then
        cd "$BASE_DIR/mcp/report"
        if npm install; then
            echo -e "${GREEN}[OK]${NC} Report MCP dependencies installed"
        else
            echo -e "${RED}${NC} npm install failed for Report MCP"
        fi
        cd "$BASE_DIR"
    fi
fi

# Install workflows and MCPs
echo ""
echo -e "${BLUE}Installing selected workflows and MCPs...${NC}"
if [ $DEVELOPER_MODE -eq 1 ]; then
    python3 "$WORKFLOWS_DIR/install-workflows.py" --developer
else
    python3 "$WORKFLOWS_DIR/install-workflows.py"
fi

echo ""

# Prepare bashrc modifications summary
BASHRC_MODIFICATIONS=()
WILL_MODIFY_BASHRC=0

# Check if blog config needs to be added
if [ -f "$WORKFLOWS_DIR/.blog-config.tmp" ]; then
    source "$WORKFLOWS_DIR/.blog-config.tmp"
    WILL_MODIFY_BASHRC=1
    BASHRC_MODIFICATIONS+=("Blog configuration (BLOG_MODE, BLOG_PATH, BLOG_NOTEBOOKS_DIR, BLOG_REPORTS_DIR)")
fi

# Check if mango alias already exists
if ! grep -q "alias mango=" ~/.bashrc 2>/dev/null; then
    WILL_MODIFY_BASHRC=1
    BASHRC_MODIFICATIONS+=("'mango' alias - launches tmux session menu anytime")
fi

# Show bashrc modification summary if needed
if [ $WILL_MODIFY_BASHRC -eq 1 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}BASHRC MODIFICATIONS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "The following will be added to ~/.bashrc:"
    for mod in "${BASHRC_MODIFICATIONS[@]}"; do
        echo "  • $mod"
    done
    echo ""
    echo -e "${YELLOW}Note: Any environment variables added by the workflow configurator"
    echo -e "have already been added to ~/.bashrc${NC}"
    echo ""
    read -p "Continue with bashrc modifications? [Y/n]: " -r
    echo

    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}Skipping bashrc modifications${NC}"
        rm -f "$WORKFLOWS_DIR/.blog-config.tmp"
    else
        # Apply blog configuration to bashrc if it was set
        if [ -f "$WORKFLOWS_DIR/.blog-config.tmp" ]; then
            echo -e "${BLUE}Applying blog configuration to ~/.bashrc...${NC}"

            # Update bashrc
            if [ -f ~/.bashrc ]; then
                # Remove old blog config if exists
                sed -i.bak '/^# Blog Configuration$/,/^$/d' ~/.bashrc

                # Add new blog config
                cat >> ~/.bashrc << EOF

# Blog Configuration
export BLOG_MODE="$BLOG_MODE"
export BLOG_PATH="$BLOG_PATH"
export BLOG_NOTEBOOKS_DIR="$NOTEBOOKS_DIR"
export BLOG_REPORTS_DIR="$REPORTS_DIR"
EOF

                echo -e "${GREEN}✓ Blog configuration added to ~/.bashrc${NC}"
            fi

            # Clean up temp file
            rm -f "$WORKFLOWS_DIR/.blog-config.tmp"
        fi

        # Add mango alias if not already present
        if ! grep -q "alias mango=" ~/.bashrc 2>/dev/null; then
            echo -e "${BLUE}Adding 'mango' alias to ~/.bashrc...${NC}"
            cat >> ~/.bashrc << 'EOF'

# Mango: Launch tmux session menu at any time
alias mango='source /home/ubuntu/mango/tmux/tmux-session-menu.sh'
EOF
            echo -e "${GREEN}✓ 'mango' alias added to ~/.bashrc${NC}"
        fi

        echo ""
        echo -e "${GREEN}Bashrc modifications complete!${NC}"
        echo -e "${YELLOW}  Run 'source ~/.bashrc' to apply changes${NC}"
        echo -e "${YELLOW}  Or start a new terminal session${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""

# Show helpful tips
if grep -q "alias mango=" ~/.bashrc 2>/dev/null; then
    echo -e "${BLUE}💡 TIP: You can now use 'mango' to launch the tmux session menu anytime!${NC}"
    echo ""
fi

# Show critical setup reminders
if [ ${#CRITICAL_SETUP_NEEDED[@]} -ne 0 ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}CRITICAL SETUP INCOMPLETE${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "The following critical features need setup:"
    for item in "${CRITICAL_SETUP_NEEDED[@]}"; do
        echo -e "  ${RED}${NC} $item"
    done
    echo ""
    echo "To enable the discuss workflow (MOST IMPORTANT FEATURE):"
    echo "  1. Run: gh auth login"
    echo "  2. Follow the authentication prompts"
    echo "  3. Test with: /discuss"
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
fi

echo "To uninstall, run: ./setup-workflows.sh --uninstall"
echo ""
