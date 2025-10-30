# Comprehensive Guide: Setting Up MCP in Claude Code

## Overview

This guide consolidates research on implementing Model Context Protocol (MCP) servers with Claude Code, based on working examples, documentation, and troubleshooting experiences from the community.

## Key Findings

### 1. Configuration File Locations

Claude Code supports three configuration scopes:

1. **Project Scope** (`.mcp.json` in project root)
   - Highest priority
   - Checked into version control
   - Shared with team members
   - Requires security approval on first use

2. **User Scope** (global configuration)
   - Cross-project accessibility
   - Private to your user
   - Added with: `claude mcp add <server-name> -s user`

3. **Local Scope** (default)
   - Available only in current folder
   - Private to you in this project

### 2. Working Configuration Format

The standard `.mcp.json` format:

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/server/index.js"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

### 3. Direct Configuration Method (Recommended)

Instead of using the CLI wizard, directly edit the `.claude.json` file in your home directory:

```json
{
  "mcpServers": {
    "my-custom-tool": {
      "type": "stdio", 
      "command": "node",
      "args": ["/home/user/mcp-tools/my-custom-tool/build/index.js"]
    }
  }
}
```

After editing, restart Claude Code to apply changes.

### 4. Adding MCP Servers

#### Using CLI Commands:
```bash
# Basic syntax
claude mcp add <name> <command> [args...]

# Add with project scope
claude mcp add shared-server -s project /path/to/server

# Add with JSON configuration
claude mcp add-json weather-api '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"]}'
```

#### Using npx packages:
```json
{
  "mcpServers": {
    "mcp-sequentialthinking-tools": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-sequentialthinking-tools"]
    }
  }
}
```

### 5. Working GitHub Examples

1. **steipete/claude-code-mcp**
   - Claude Code as one-shot MCP server
   - Permissions bypassed automatically
   - Comprehensive testing infrastructure

2. **auchenberg/claude-code-mcp**
   - Full Claude Code capabilities via MCP
   - TypeScript SDK implementation
   - File operations, shell commands, code analysis

3. **KunihiroS/claude-code-mcp**
   - Multiple tools: explain_code, review_code, fix_code, etc.
   - Base64 encoding for stability
   - NPX installation: `@kunihiros/claude-code-mcp`

4. **SDGLBL/mcp-claude-code**
   - Direct file modification capabilities
   - Project improvement features

### 6. Known Issues and Solutions

#### Issue 1: Protocol Version Validation Error
- **Problem**: protocolVersion validation fails despite correct configuration
- **Status**: Known bug in Claude Code CLI (v0.2.69+)
- **Workaround**: Use direct configuration file editing

#### Issue 2: Environment Variables Not Passed
- **Problem**: `env` section variables not passed to MCP servers
- **Workaround**: Pass as command arguments or use .env files

#### Issue 3: Windows Path Issues
- **Problem**: npx fails on Windows due to PATH differences
- **Solution**: Use absolute paths to Node.js executable

#### Issue 4: Tool Name Validation
- **Problem**: API error for invalid tool names
- **Solution**: Use only alphanumeric, underscore, and hyphen characters

### 7. Troubleshooting Steps

1. **Use absolute paths** for all commands and scripts
2. **Edit configuration directly** in `.claude.json` 
3. **Restart Claude Code** after changes
4. **Check tool naming** conventions
5. **Verify with**: `/mcp` command in Claude Code
6. **For Windows**: Use full Node.js path instead of npx

### 8. Environment Setup Requirements

#### First-time setup:
```bash
# One-time requirement for Claude CLI
claude --dangerously-skip-permissions
```

#### Environment variables (alternative methods):
1. Command line arguments
2. `.env` files in project directory
3. `~/.claude-code-mcp.env` in home directory
4. Direct configuration in MCP host settings

### 9. Recent Updates (2025)

- Claude Code version 0.2.126 (latest stable)
- Security fixes for tar-fs vulnerability
- Support for Stripe, Cloudflare, Supabase integrations
- Three-scope configuration system
- Direct JSON configuration support

### 10. Best Practices

1. **Start with project scope** for team collaboration
2. **Use stdio transport** for local servers
3. **Implement proper error handling** in servers
4. **Version control** `.mcp.json` files
5. **Document** required environment variables
6. **Test** configurations before team deployment

## Example: Complete Working Setup

1. Create `.mcp.json` in project root:
```json
{
  "mcpServers": {
    "project-tools": {
      "type": "stdio",
      "command": "node",
      "args": ["/Users/username/mcp-servers/project-tools/index.js"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

2. Or add via CLI:
```bash
claude mcp add project-tools -s project node /Users/username/mcp-servers/project-tools/index.js
```

3. Verify connection:
```
# In Claude Code
/mcp

# Should show:
MCP Server Status
- project-tools: connected
```

## Conclusion

While MCP integration in Claude Code has some known issues (particularly with environment variables and protocol validation), the stdio-based approach works reliably when using absolute paths and direct configuration file editing. The community has developed multiple working implementations that demonstrate successful integration patterns.