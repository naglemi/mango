# Sleep MCP

A minimal, focused Model Context Protocol (MCP) server for blocking until processes complete.

## Purpose

This MCP enables Claude Code to **wait synchronously** until a process finishes. Unlike `process-monitor` which includes notifications, crash reports, and W&B integration, `sleep` is intentionally minimal - just pure blocking until exit.

## Use Cases

- **Wait for a command to finish** before continuing with next steps
- **Block execution** until a background process completes
- **Simple process synchronization** without monitoring overhead
- **Wait for the last invoked tool** to complete before proceeding

## Key Features

### Minimalist Design
- **No notifications**: Silent operation, no Pushover alerts
- **No crash reports**: No email integration
- **No W&B integration**: No metrics tracking
- **Pure blocking**: Just waits until process exits or timeout

### Tools Available

#### `sleep_until_complete`
Block until a specific PID completes or timeout occurs.

**Parameters:**
- `pid` (required): Process ID to wait for
- `timeout` (optional): Maximum wait time in seconds (default: 7200 = 2 hours)
- `poll_interval` (optional): Check frequency in seconds (default: 1.0)

**Returns:**
- `status: "completed"` - Process exited
- `status: "timeout"` - Timeout reached, process still running
- `status: "not_found"` - Process not found at start

**Example:**
```python
# Wait for process 12345 to complete
result = await runMCP('sleep', 'sleep_until_complete', {
    'pid': 12345
})
```

#### `sleep_until_command_complete`
Block until all processes matching a command pattern complete.

**Parameters:**
- `command_pattern` (required): Substring to match in command line
- `timeout` (optional): Maximum wait time in seconds (default: 7200)
- `poll_interval` (optional): Check frequency in seconds (default: 1.0)

**Returns:**
- `status: "completed"` - All matching processes exited
- `status: "timeout"` - Timeout reached, some still running
- `status: "not_found"` - No matching processes found at start

**Example:**
```python
# Wait for all Python training scripts to complete
result = await runMCP('sleep', 'sleep_until_command_complete', {
    'command_pattern': 'python train.py'
})
```

#### `quick_check`
Quick, non-blocking check if a process is running.

**Parameters:**
- `pid` (required): Process ID to check

**Returns:**
- `running`: Boolean indicating if process exists
- `command`: Command line (if running)

**Example:**
```python
# Quick check if process is running
status = await runMCP('sleep', 'quick_check', {
    'pid': 12345
})
```

## Design Philosophy

### Why a separate "sleep" MCP?

The existing `process-monitor` MCP is feature-rich with notifications, crash reports, W&B integration, and complex timeout handling. Sometimes you just want to **block until a process completes** without any extra features.

**Use `sleep` when you want:**
- Simple blocking behavior
- Minimal token usage (silent operation)
- No notifications or reports
- Wait for command patterns (not just PIDs)

**Use `process-monitor` when you want:**
- Pushover notifications for long-running jobs
- Crash reports via email
- W&B metrics integration
- Hourly progress updates

## Installation

Add to `setup-claude.sh`:

```bash
# Add sleep MCP
echo "  Adding sleep MCP..."
SLEEP_SERVER_PATH="$(realpath "$SCRIPT_DIR/mcp/sleep/sleep_mcp_server.py")"

if claude mcp add sleep --scope user -- "$PYTHON_CMD" "$SLEEP_SERVER_PATH"; then
    echo -e "  ${GREEN}${NC} sleep MCP added"
else
    echo -e "  ${RED}${NC} Failed to add sleep MCP"
    exit 1
fi
```

## Implementation Details

- **Process detection**: Uses `os.kill(pid, 0)` (no actual signal sent)
- **Command lookup**: Reads `/proc/{pid}/cmdline` on Linux
- **Poll frequency**: Default 1 second for responsiveness
- **Silent operation**: No output during wait to preserve context
- **Structured responses**: JSON format for easy parsing

## Comparison with process-monitor

| Feature | sleep | process-monitor |
|---------|-------|-----------------|
| Block until complete |  |  |
| Pushover notifications |  |  |
| Email crash reports |  |  |
| W&B integration |  |  |
| Hourly progress updates |  |  |
| Wait by command pattern |  |  |
| Default timeout | 2 hours | 1hr 55min |
| Default poll interval | 1 second | 5 seconds |
| Context usage | Minimal | Moderate |

## Example Workflows

### Wait for a specific process
```python
# Start a background process
pid = launch_training()

# Block until it completes
result = await runMCP('sleep', 'sleep_until_complete', {'pid': pid})

# Continue with next steps
if result['status'] == 'completed':
    analyze_results()
```

### Wait for any matching command
```python
# Launch multiple training runs
for config in configs:
    launch_training(config)

# Wait for all to complete
result = await runMCP('sleep', 'sleep_until_command_complete', {
    'command_pattern': 'train.py'
})
```

### Check without blocking
```python
# Quick check if still running
status = await runMCP('sleep', 'quick_check', {'pid': pid})

if status['running']:
    print("Still running, come back later")
else:
    print("Completed, process results")
```

## Error Handling

- Invalid PIDs return clear error messages
- Process not found scenarios handled gracefully
- Timeout returns status with elapsed time
- Permission errors handled (treats as "exists")

## Compatibility

- **Linux**: Full functionality via `/proc` filesystem
- **macOS**: Limited functionality (quick_check only)
- **Windows**: Not supported

## Technical Notes

- **Blocking nature**: This tool WILL block Claude Code execution
- **Use responsibly**: Don't wait for processes that may never complete
- **Consider timeouts**: Always set reasonable timeout values
- **Pattern matching**: `sleep_until_command_complete` uses substring matching
