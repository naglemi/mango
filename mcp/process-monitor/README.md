# Process Monitor MCP

A Model Context Protocol (MCP) server for monitoring long-running processes in Claude Code with smart timeout handling.

## Purpose

This MCP enables Claude Code to:
- Monitor background processes until completion
- Handle Claude Code's 2-hour foreground process limit gracefully
- Provide process status checks without blocking
- Find recent processes for monitoring

## Key Features

### Smart Timeout Handling
- **Default timeout: 1hr 55min** to avoid Claude Code's 2hr system limit
- **Monitor timeout ≠ Process completion**: When the monitor times out, the background process may still be running
- Returns clear status indicating whether timeout was due to monitor limits or actual process completion

### Tools Available

#### `monitor_process`
Monitors a process until completion or timeout (1hr 55min by default).

**Parameters:**
- `pid` (required): Process ID to monitor
- `timeout` (optional): Maximum monitoring time in seconds (default: 6900 = 1hr 55min)
- `poll_interval` (optional): How often to check process status in seconds (default: 5)

**Returns:**
- `status: "completed"` - Process has exited
- `status: "monitor_timeout"` - Monitor reached time limit (process may still be running)

#### `check_process`
Quick, non-blocking check if a process is running.

**Parameters:**
- `pid` (required): Process ID to check

#### `find_recent_processes`
Find recent processes that might be candidates for monitoring.

**Parameters:**
- `pattern` (optional): Filter pattern for process names
- `limit` (optional): Maximum number of processes to return (default: 10)

## Integration with `/chill_until_it_finishes`

This MCP is designed to work with the `/chill_until_it_finishes` slash command:

1. Command identifies target process
2. Starts monitoring via this MCP
3. On timeout: Restarts monitoring automatically
4. On completion: Triggers result analysis and reporting

## Installation

The process-monitor MCP is automatically installed by the setup scripts:
- `setup-claude.sh` (for Claude Code)
- `setup-cascade-mcp.sh` (for Windsurf Cascade)

## System Constraints

 **IMPORTANT**: Claude Code enforces a 2-hour timeout for ALL foreground processes. This MCP times out at 1hr 55min to prevent system termination.

### What This Means
- Monitor timeout ≠ Your process finishing
- Your background process continues running independently
- The `/chill_until_it_finishes` command handles restarts automatically

## Example Usage

```python
# Monitor a specific process
result = await runMCP('process-monitor', 'monitor_process', {
    'pid': 12345,
    'timeout': 6900,  # 1hr 55min
    'poll_interval': 5  # Check every 5 seconds
})

# Quick status check
status = await runMCP('process-monitor', 'check_process', {
    'pid': 12345
})

# Find processes to monitor
processes = await runMCP('process-monitor', 'find_recent_processes', {
    'pattern': 'python',
    'limit': 5
})
```

## Error Handling

- Invalid PIDs return appropriate error messages
- Process not found scenarios are handled gracefully
- System errors (permissions, etc.) are captured and reported
- Timeout scenarios clearly distinguish between monitor and process timeouts

## Compatibility

- **Linux**: Full functionality using `/proc` filesystem
- **macOS**: Basic functionality using `ps` command
- **Windows**: Limited functionality (may require adjustments)

## Technical Details

- Uses `os.kill(pid, 0)` for process existence checks (no actual signals sent)
- Polls every 5 seconds by default to balance responsiveness and system load
- Returns structured JSON responses for easy parsing
- Handles edge cases like permission errors and invalid PIDs
- Designed for silent operation during monitoring (no token flooding)