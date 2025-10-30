# Claude Code MCP Setup - ACTUAL Working Method

## IMPORTANT: .mcp.json Does NOT Work!

The documentation about `.mcp.json` is outdated. Claude Code uses its own MCP management system via the `claude mcp` command.

## Correct Setup Method

### 1. Run the Setup Script
```bash
cd /path/to/usability
./setup-claude-mcp.sh
```

This script will:
- Install dependencies
- Use `claude mcp add-json` to configure servers
- Set up both Pushover and Report MCPs

### 2. What the Script Does

The script uses these commands:
```bash
# Add Pushover MCP
claude mcp add-json pushover '{
  "command": "npx",
  "args": ["-y", "pushover-mcp"],
  "env": {
    "PUSHOVER_APP_TOKEN": "your-token",
    "PUSHOVER_USER_KEY": "your-key"
  }
}' -s local

# Add Report MCP
claude mcp add-json report '{
  "command": "node",
  "args": ["/path/to/mcp/report/index.js"],
  "env": {
    "REPORT_BUCKET": "usability-reports",
    "AWS_REGION": "us-east-1",
    "REPORT_EMAIL_FROM": "email@example.com",
    "REPORT_EMAIL_TO": "email@example.com"
  }
}' -s local
```

### 3. Verify Setup
```bash
# List configured servers
claude mcp list

# Should show:
pushover: npx -y pushover-mcp
report: node /path/to/mcp/report/index.js
```

### 4. Restart Claude Code
After setup, restart Claude Code completely.

### 5. Check in Claude Code
Run `/mcp` - should show:
```
⎿ MCP Server Status ⎿
⎿ • pushover: connected ⎿
⎿ • report: connected ⎿
```

## Manual Commands

### Add a server:
```bash
claude mcp add <name> <command> [args...]
claude mcp add-json <name> <json-config>
```

### Remove a server:
```bash
claude mcp remove <name> -s local
```

### List servers:
```bash
claude mcp list
```

### Reset approvals:
```bash
claude mcp reset-project-choices
```

## Troubleshooting

If `/mcp` shows "No MCP servers configured":
1. Run `claude mcp list` in terminal
2. If empty, run the setup script again
3. Restart Claude Code
4. The servers should appear

## Key Points

1. **DO NOT** rely on `.mcp.json` files
2. **DO** use `claude mcp` commands
3. **Servers are project-local** when using `-s local`
4. **Environment variables** must be in the JSON config

## Why .mcp.json Doesn't Work

Claude Code's current version doesn't automatically read `.mcp.json` files. It maintains its own configuration via the `claude mcp` command-line interface. The `.mcp.json` approach may have worked in earlier versions but is no longer supported.