# Pushover MCP Integration

This repository includes scripts to set up Pushover notifications through MCP (Model Context Protocol) for all major AI coding assistants.

## What is MCP?

Model Context Protocol (MCP) is a standardized way for AI assistants to interact with external tools and services. It allows AI assistants to send notifications, access databases, control browsers, and more.

## Setup

Run the setup script to configure Pushover MCP for all supported AI assistants:

```bash
./setup-pushover-mcp.sh
```

This will:
1. Install the `@ashiknesin/pushover-mcp` package globally
2. Configure MCP for:
   - Claude Code (project-level `.mcp.json`)
   - Claude Desktop (global config)
   - Cursor (project-level `.cursor/mcp.json`)
   - Windsurf (global config)
   - Roo Code (both global and project configs)

## How AI Assistants Can Use It

Once configured, AI assistants can send push notifications by using the MCP tool. For example:

- "Send a notification saying 'Build completed successfully'"
- "Send a push notification with the title 'Test Results' saying 'All 50 tests passed'"
- "Notify me when the training is complete"

The AI assistant will automatically use the `send_notification` tool provided by the Pushover MCP server.

## Manual Usage

For manual notifications (outside of AI assistants), use the provided wrapper script:

```bash
# Simple notification
./pushover-notify.sh "Build completed"

# With title
./pushover-notify.sh -t "Build Status" "All tests passed"

# Markdown file (like the Python script)
./pushover-notify.sh -m -t "Ninja Report" ./scrolls/analysis.md

# Page mode (uses question sounds)
./pushover-notify.sh --page -t "Need Input" "Should I proceed?"

# Custom sound
./pushover-notify.sh -s idle1 "Background task finished"
```

## Comparison with Python Script

The MCP integration provides similar functionality to your Python script:

| Feature | Python Script | MCP Integration |
|---------|--------------|-----------------|
| Send notifications |  |  |
| Markdown support |  |  (through AI conversion) |
| Custom sounds |  |  |
| Page mode |  |  (AI can specify) |
| Direct AI usage |  |  |
| Manual usage |  |  (via wrapper) |

## Configuration Details

### Credentials

The scripts use the same default credentials as your Python script:
- App Token: `azottw766yxy7oz3vsu2oz432brx8f`
- User Key: `uqek4s2jo8pmrkskp96ravqb85yr15`

You can override these when running the setup script.

### MCP Server Details

The Pushover MCP server provides:
- Tool: `send_notification`
- Parameters:
  - `message` (required): The notification message
  - `title` (optional): Notification title
  - `priority` (optional): -2 to 2
  - `sound` (optional): Notification sound
  - `device` (optional): Specific device name

## Notes

1. **AI Assistant Integration**: Once set up, AI assistants can send notifications autonomously without needing to run external scripts.

2. **Project vs Global**: Some configs are project-specific (committed to git) while others are global (user-specific).

3. **First Use**: Some AI assistants may ask for approval when first using the MCP tool.

4. **Restart Required**: Claude Desktop needs to be restarted after configuration.

5. **OpenAI Codex**: Currently has limited MCP support. You may need to continue using the Python script directly with Codex.

## Troubleshooting

- If notifications aren't working, check that the npm package is installed: `npm list -g @ashiknesin/pushover-mcp`
- Verify credentials are correct in the configuration files
- Check AI assistant logs for MCP connection errors
- Ensure you've approved the MCP server in assistants that require approval