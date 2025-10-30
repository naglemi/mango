#!/usr/bin/env bash
# Automated MCP setup for Windsurf Cascade
# Installs dependencies and registers Pushover + Report servers in the user scope

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

printf "${BLUE}▶ Cascade MCP automated setup${NC}\n"

# 1. Ensure Node/npm present
if ! command -v node &>/dev/null; then
  printf "${YELLOW}Node.js not found – please install Node ≥ 18 and re-run.${NC}\n" >&2
  exit 1
fi

# 2. Install local deps for Report MCP
printf "${BLUE}Installing report MCP dependencies…${NC}\n"
(cd "$SCRIPT_DIR/report" && npm ci --silent)
printf "${GREEN} Report deps installed${NC}\n"

# 3. Ensure global pushover-mcp installed
if ! command -v pushover-mcp &>/dev/null; then
  printf "${BLUE}Installing pushover-mcp globally…${NC}\n"
  npm install -g pushover-mcp
fi
printf "${GREEN} pushover-mcp available${NC}\n"

# 4. Write MCP config to ~/.codeium/windsurf/mcp_config.json

# 4. Ensure ninjagrab.sh is in project root
if [ ! -f "$PROJECT_ROOT/ninjagrab.sh" ]; then
  printf "${BLUE}Copying ninjagrab.sh to project root…${NC}\n"
  if [ -f "$PROJECT_ROOT/workflows/ninjagrab.sh" ]; then
    cp "$PROJECT_ROOT/workflows/ninjagrab.sh" "$PROJECT_ROOT/"
    chmod +x "$PROJECT_ROOT/ninjagrab.sh"
    printf "${GREEN} ninjagrab.sh copied and made executable${NC}\n"
  else
    printf "${YELLOW} ninjagrab.sh not found in workflows/ - MCP will use Python fallback${NC}\n"
  fi
fi

# 5. Build global MCP config JSON
CONFIG_DIR="$HOME/.codeium/windsurf"
CONFIG_FILE="$CONFIG_DIR/mcp_config.json"
mkdir -p "$CONFIG_DIR"

# env vars (provide defaults to avoid empty)
PUSHOVER_APP_TOKEN="${PUSHOVER_APP_TOKEN:-change-me}"
PUSHOVER_USER_KEY="${PUSHOVER_USER_KEY:-change-me}"
AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
REPORT_BUCKET="${REPORT_BUCKET:-usability-reports}"
REPORT_EMAIL_FROM="${REPORT_EMAIL_FROM:-slurmalerts1017@gmail.com}"
REPORT_EMAIL_TO="${REPORT_EMAIL_TO:-slurmalerts1017@gmail.com}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Resolve absolute paths before writing config
REPORT_SERVER_PATH="$(realpath "$SCRIPT_DIR/report/index.js")"
NINJAGRAB_SERVER_PATH="$(realpath "$SCRIPT_DIR/ninjagrab/ninjagrab_mcp_server.py")"
NINJAGRAB_SCRIPT_PATH="$(realpath "$PROJECT_ROOT/ninjagrab.sh")"
PROCESS_MONITOR_SERVER_PATH="$(realpath "$SCRIPT_DIR/process-monitor/process_monitor_mcp_server.py")"
MISALIGNMENT_ALARM_SERVER_PATH="$(realpath "$SCRIPT_DIR/misalignment-alarm/misalignment_alarm_mcp_server.py")"
O3_PROXY_SERVER_PATH="$(realpath "$SCRIPT_DIR/o3-proxy/o3_proxy_mcp_server.py")"
GRAB_WANDB_LOG_SERVER_PATH="$(realpath "$SCRIPT_DIR/grab_wandb_log/grab_wandb_log_mcp_server.py")"
WANDB_TOOLS_DIR="/home/ubuntu/finetune_safe/wandb_tools"

cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "pushover-notify": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "pushover-mcp", "start", "--token", "$PUSHOVER_APP_TOKEN", "--user", "$PUSHOVER_USER_KEY"]
    },
    "report-s3": {
      "type": "stdio",
      "command": "node",
      "args": ["$REPORT_SERVER_PATH"],
      "env": {
        "REPORT_BUCKET": "$REPORT_BUCKET",
        "AWS_REGION": "$AWS_DEFAULT_REGION",
        "REPORT_EMAIL_FROM": "$REPORT_EMAIL_FROM",
        "REPORT_EMAIL_TO": "$REPORT_EMAIL_TO",
        "REPORT_URL_EXPIRATION": "604800"
      }
    },
    "ninjagrab": {
      "type": "stdio",
      "command": "python",
      "args": ["$NINJAGRAB_SERVER_PATH"],
      "env": {
        "NINJAGRAB_SCRIPT_PATH": "$NINJAGRAB_SCRIPT_PATH"
      }
    },
    "process-monitor": {
      "type": "stdio",
      "command": "python",
      "args": ["$PROCESS_MONITOR_SERVER_PATH"]
    },
    "misalignment-alarm": {
      "type": "stdio",
      "command": "python",
      "args": ["$MISALIGNMENT_ALARM_SERVER_PATH"]
    },
    "o3-proxy": {
      "type": "stdio",
      "command": "python",
      "args": ["$O3_PROXY_SERVER_PATH"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    },
    "grab-wandb-log": {
      "type": "stdio",
      "command": "python",
      "args": ["$GRAB_WANDB_LOG_SERVER_PATH"],
      "env": {
        "WANDB_TOOLS_DIR": "$WANDB_TOOLS_DIR"
      }
    }
  }
}
EOF

printf "${GREEN} Wrote MCP configuration to $CONFIG_FILE${NC}\n"

printf "\n${YELLOW} Restart Windsurf Cascade and press the Refresh button in the Plugins pane to load the new servers.${NC}\n"
