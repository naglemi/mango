# MCP Module

Model Context Protocol servers for AI assistant integrations, providing notification and reporting capabilities.

##  CRITICAL: Set Environment Variables FIRST!

**Before doing ANYTHING else, you MUST set these environment variables in your ~/.bashrc:**

```bash
# Add these to ~/.bashrc (get your tokens from https://pushover.net/)
export PUSHOVER_APP_TOKEN="your-pushover-app-token-here"
export PUSHOVER_USER_KEY="your-pushover-user-key-here"

# Then reload your shell
source ~/.bashrc
```

Without these environment variables, Pushover MCP WILL NOT WORK!

## Setup Method Has Changed!

**`.mcp.json` files are OUTDATED**. Claude Code now requires using the `claude mcp` CLI commands.

### Quick Setup (AFTER setting env vars):
```bash
cd usability
./setup-claude-mcp.sh
```

This will configure both Pushover and Report MCPs using the correct method.

## Overview

MCP (Model Context Protocol) allows AI assistants like Claude to use external tools. This module provides three working MCP servers:

1. **Pushover** - Send push notifications to mobile devices  
2. **Report** - Create S3-based reports with email notifications
3. **o3-proxy** - "Phone a friend" consultation with OpenAI's o3 reasoning model

**Note**: GitHub MCP was attempted but does not work. See "GitHub MCP (DOES NOT WORK)" section below.

##  CRITICAL FOR AI AGENTS

**MCP Tools ARE Available - But Must Be Configured First!**

1. Tools appear with `mcp__` prefix:
   - `mcp__report-s3__send_report`
   - `mcp__pushover-notify__send_notification`

2. If tools are missing:
   - Run: `cd usability && ./setup-claude-mcp.sh`
   - Human must restart Claude Code
   - Tools will then be available

3. Common issues:
   - `.mcp.json` files are OBSOLETE - use `claude mcp` commands
   - Environment variables must be in the add-json command
   - Human MUST restart Claude Code after setup

See [MCP_AUTONOMOUS_AGENT.md](../MCP_AUTONOMOUS_AGENT.md) for complete agent guide.

## Pushover MCP

### What It Does
- Sends instant push notifications to your phone/tablet
- Supports markdown formatting in messages
- Configurable priority levels and sounds
- Perfect for long-running task notifications

### Setup

1. **Get Pushover Account** (one-time $5 purchase)
   - Install Pushover app on your device
   - Create account at https://pushover.net
   - Note your User Key from the dashboard

2. **Create Application**
   - Go to https://pushover.net/apps
   - Create new application (e.g., "AI Assistant")
   - Note the API Token

3. **Configure MCP**
```bash
cd mcp/pushover
./setup-pushover-mcp.sh

# Enter when prompted:
# - Pushover User Key: uqek4s2jo8pmrk...
# - Pushover App Token: azottw766yxy7o...
```

### Usage

#### From Command Line
```bash
# Simple notification
./mcp/pushover/pushover-notify.sh "Build complete!"

# With title
./mcp/pushover/pushover-notify.sh -t "CI/CD" "All tests passed"

# High priority with sound
./mcp/pushover/pushover-notify.sh -p 1 -s success "Deployment successful!"

# Markdown formatting
./mcp/pushover/pushover-notify.sh -f markdown "**Bold** and _italic_ text"
```

#### From AI Assistant
Once configured, AI can send notifications naturally:
- "Send a notification that the training is complete"
- "Alert me that all tests passed with high priority"
- "Notify with sound 'success' that deployment finished"

### Options
- `-t` - Title (default: "AI Agent Notification")
- `-p` - Priority: -2 (silent) to 2 (emergency)
- `-s` - Sound: pushover, bike, bugle, cashregister, classical, etc.
- `-f` - Format: markdown or html

## Report MCP

### What It Does
- Creates organized reports in S3 with file attachments
- Sends email notifications with report summaries
- Handles images, logs, and large files efficiently
- Provides pre-signed URLs for secure access
- Organizes reports by agent name and timestamp

### Prerequisites

####  For Michael Nagle (Primary User)
**Everything is already set up!** You have:
-  S3 bucket: `usability-reports`
-  Verified email: `slurmalerts1017@gmail.com`
-  AWS credentials in your shell config

Just use these existing resources when running setup.

#### For Other Users
- AWS account with S3 and SES access
- Verified email address in SES
- AWS credentials configured

### Setup

####  Quick Setup for Michael Nagle
```bash
./setup-report-mcp.sh

# Enter when prompted:
# - S3 bucket name: usability-reports
# - From email: slurmalerts1017@gmail.com
# - To email: slurmalerts1017@gmail.com
```

**That's it!** No need to create buckets or verify emails.

#### Setup for Other Users

1. **Configure AWS Credentials**
```bash
# Add to ~/.bashrc or ~/.zshrc:
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

2. **Create S3 Bucket**
```bash
cd mcp/report
node create-bucket.js my-reports-bucket
```

3. **Verify Email in SES**
```bash
# Interactive verification
./verify-ses-email.sh

# Or direct verification
node verify-email-direct.js myemail@example.com
# Then click the link in your email
```

4. **Install Report MCP**
```bash
./setup-report-mcp.sh

# Enter when prompted:
# - S3 bucket name: my-reports-bucket
# - From email: alerts@example.com
# - To email: myemail@example.com
```

### Usage

#### From AI Assistant
AI can create reports naturally:
- "Send a report with the training results and loss plots"
- "Create a report titled 'Model Performance' with these images"
- "Send report with all log files from today's run"

#### Testing
```bash
# Test with sample data
cd mcp/report
node test-report-mcp.js

# You'll receive an email with:
# - Report summary
# - Link to full report
# - All attached files accessible
```

### Report Structure
Reports are organized in S3:
```
bucket/
└── AgentName/
    └── 2024-01-15_14-30-45/
        ├── index.html      # Report viewer
        ├── image1.png      # Attached files
        ├── image2.png
        └── results.log
```

### Features
- **Smart Email**: Summary in email, full report in S3
- **Pre-signed URLs**: Secure 7-day access to files
- **Image Preview**: Images display inline in reports
- **Auto-organization**: By agent name and timestamp
- **Large Files**: No email size limits

## GitHub MCP (DOES NOT WORK)

###  WARNING: GitHub MCP is broken due to Microsoft's incompetence

After Microsoft's acquisition of GitHub, their typical pattern of ruining perfectly good products continues. The GitHub MCP server is fundamentally broken and cannot be made to work with Claude Code.

### Everything We Tried (All Failed)

1. **Official NPM package** (`@modelcontextprotocol/server-github`)
   - Result: "Connection closed" errors
   - Reason: Package exists but doesn't work

2. **Direct npx execution**
   - `npx -y @modelcontextprotocol/server-github`
   - Result: Connection immediately closes
   
3. **Wrapper scripts** (multiple attempts)
   - Shell wrappers to handle environment variables
   - Python wrappers to massage the configuration
   - Result: All failed with connection errors

4. **HTTP endpoint** (`https://api.githubcopilot.com/mcp/`)
   - Result: "Dynamic client registration failed: HTTP 404"
   - Reason: Microsoft's endpoint doesn't implement required OAuth flow

5. **SSE transport**
   - Result: Still broken
   - Reason: Same OAuth issues

6. **Local installation**
   - Installing package locally and running directly
   - Result: Entry point issues, connection failures

7. **Docker approach**
   - Result: Not even attempted after all other failures

8. **Every possible token configuration**
   - `GITHUB_PERSONAL_ACCESS_TOKEN`
   - `GITHUB_PAT`
   - Hardcoded tokens
   - Tokens in headers
   - Result: "No token data found" or connection closed

### Root Cause: Microsoft's Incompetence

The GitHub MCP server is a perfect example of Microsoft's approach to software:
- Half-baked implementation
- No working examples
- Contradictory documentation
- OAuth requirements that don't work
- Classic Microsoft "ship it broken, maybe fix it later" mentality

### What To Use Instead

**Use the GitHub CLI** - It actually works:

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Use it
gh repo list
gh issue list
gh pr list
# etc.
```

The GitHub CLI is reliable, well-documented, and actually maintained. Unlike the MCP server, it wasn't ruined by Microsoft's touch.

### Lessons Learned

1. Never trust Microsoft products
2. Never trust products acquired by Microsoft  
3. When Microsoft says "enterprise ready", run
4. The simpler the Microsoft solution looks, the more broken it is
5. Microsoft's idea of "integration" is "make it so complex it never works"

## MCP Configuration

###  IMPORTANT: Configuration Method Has Changed!

**DO NOT USE `.mcp.json` files** - they are ignored by Claude Code.

Instead, use the `claude mcp` CLI commands:

```bash
# Add Pushover MCP
claude mcp add-json pushover-notify '{
  "command": "npx",
  "args": ["-y", "pushover-mcp"],
  "env": {
    "PUSHOVER_APP_TOKEN": "your-app-token",
    "PUSHOVER_USER_KEY": "your-user-key"
  }
}' -s local

# Add Report MCP
claude mcp add-json report-s3 '{
  "command": "node",
  "args": ["/absolute/path/to/usability/mcp/report/index.js"],
  "env": {
    "REPORT_BUCKET": "usability-reports",
    "AWS_REGION": "us-east-1",
    "REPORT_EMAIL_FROM": "slurmalerts1017@gmail.com",
    "REPORT_EMAIL_TO": "slurmalerts1017@gmail.com",
    "REPORT_URL_EXPIRATION": "604800"
  }
}' -s local
```

Or simply run: `cd usability && ./setup-claude-mcp.sh`
```

## Examples

### Example 1: Training Notification
```bash
# AI completes model training
# AI: "I'll notify you that training is complete"
# Sends: High priority notification with training metrics
```

### Example 2: Error Report
```bash
# AI encounters errors during processing
# AI: "I'll send a report with the error logs"
# Creates: S3 report with full logs, emails summary
```

### Example 3: Daily Summary
```bash
# Scheduled task completion
./mcp/pushover/pushover-notify.sh \
  -t "Daily Summary" \
  -f markdown \
  "**Completed**: 15 tasks\n**Failed**: 0\n**Time**: 2.5 hours"
```

## Troubleshooting

### Pushover Issues
- **No notification**: Check User Key and App Token
- **Invalid format**: Use -f markdown for formatting
- **Rate limits**: Max 10,000 messages/month

### Report Issues
- **Access Denied**: Check S3 bucket permissions
- **Email not sent**: Verify address in SES
- **Large files slow**: Normal - uses pre-signed URLs
- **Images not showing**: Check total size < 10MB for embedded images
- **Email too large**: SES limit is 10MB total, including base64 encoding overhead

## Security Notes

- Pushover tokens are stored in `.mcp.json` (gitignored)
- AWS credentials should use IAM with minimal permissions
- Pre-signed URLs expire after 7 days
- Email addresses must be verified in SES

## Files in This Module

```
mcp/
├── README.md           # This file
├── pushover/
│   ├── setup-pushover-mcp.sh
│   ├── pushover-notify.sh
│   └── MCP-PUSHOVER.md
└── report/
    ├── index.js        # MCP server implementation
    ├── package.json    # Dependencies
    ├── setup-report-mcp.sh
    ├── setup-grape-reports.sh
    ├── test-report-mcp.js
    ├── create-bucket.js
    ├── verify-email-direct.js
    └── verify-ses-email.sh
```