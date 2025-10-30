#!/usr/bin/env python3
"""
Sleep MCP Server for Claude Code

A simple, focused MCP that blocks until a specified process completes.
Unlike process-monitor, this is intentionally minimal - no notifications,
no reports, just pure blocking until process exit.

Use cases:
- Wait for a command/script to finish before continuing
- Block Claude Code execution until a background process completes
- Simple process synchronization without monitoring overhead
"""

import json
import sys
import os
import time
from datetime import datetime


def send_message(message):
    """Send a JSON-RPC message to stdout"""
    print(json.dumps(message))
    sys.stdout.flush()


def receive_message():
    """Receive a JSON-RPC message from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def process_exists(pid):
    """Check if process exists without killing it"""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # Process exists but we can't access it
    except ValueError:
        return False  # Invalid PID


def get_process_command(pid):
    """Get the command line for a process (Linux only)"""
    try:
        proc_path = f"/proc/{pid}/cmdline"
        if os.path.exists(proc_path):
            with open(proc_path, 'r') as f:
                cmdline = f.read().replace('\x00', ' ').strip()
                return cmdline if cmdline else "unknown"
    except:
        pass
    return "unknown"


def handle_initialize(params):
    """Handle initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "sleep",
            "version": "1.0.0"
        }
    }


def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "sleep_until_complete",
                "description": "Block until a process completes or timeout occurs. Returns immediately if process not found.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to wait for"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum time to wait in seconds (default: 7200 = 2 hours)",
                            "default": 7200
                        },
                        "poll_interval": {
                            "type": "number",
                            "description": "How often to check process status in seconds (default: 1.0)",
                            "default": 1.0
                        }
                    },
                    "required": ["pid"]
                }
            },
            {
                "name": "sleep_until_command_complete",
                "description": "Block until all processes matching a command pattern complete or timeout. Useful when you don't have the exact PID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command_pattern": {
                            "type": "string",
                            "description": "Command pattern to search for (substring match in command line)"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum time to wait in seconds (default: 7200 = 2 hours)",
                            "default": 7200
                        },
                        "poll_interval": {
                            "type": "number",
                            "description": "How often to check process status in seconds (default: 1.0)",
                            "default": 1.0
                        }
                    },
                    "required": ["command_pattern"]
                }
            },
            {
                "name": "quick_check",
                "description": "Quick non-blocking check if a process is running. Returns immediately.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to check"
                        }
                    },
                    "required": ["pid"]
                }
            }
        ]
    }


def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name == "sleep_until_complete":
        return sleep_until_complete(arguments)
    elif name == "sleep_until_command_complete":
        return sleep_until_command_complete(arguments)
    elif name == "quick_check":
        return quick_check(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


def sleep_until_complete(arguments):
    """Block until a specific PID completes"""
    pid = arguments.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid PID")

    timeout = arguments.get("timeout", 7200)  # 2 hours default
    poll_interval = arguments.get("poll_interval", 1.0)

    start_time = time.time()

    # Check if process exists at start
    if not process_exists(pid):
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "pid": pid,
                        "status": "not_found",
                        "message": f"Process {pid} not found or already exited",
                        "start_time": datetime.now().isoformat()
                    }, indent=2)
                }
            ]
        }

    # Get initial command for reference
    initial_command = get_process_command(pid)

    # Silent blocking loop - no output during wait to preserve context
    while True:
        elapsed = time.time() - start_time

        # Check if process still exists
        if not process_exists(pid):
            # Process completed!
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "pid": pid,
                            "status": "completed",
                            "command": initial_command,
                            "elapsed_seconds": int(elapsed),
                            "end_time": datetime.now().isoformat(),
                            "message": f"Process {pid} completed after {int(elapsed)} seconds"
                        }, indent=2)
                    }
                ]
            }

        # Check for timeout
        if elapsed >= timeout:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "pid": pid,
                            "status": "timeout",
                            "command": initial_command,
                            "timeout_seconds": timeout,
                            "elapsed_seconds": int(elapsed),
                            "still_running": True,
                            "end_time": datetime.now().isoformat(),
                            "message": f"Timeout reached after {timeout} seconds. Process {pid} still running."
                        }, indent=2)
                    }
                ]
            }

        # Sleep before next check
        time.sleep(poll_interval)


def find_processes_by_command(command_pattern):
    """Find all PIDs matching a command pattern"""
    matching_pids = []

    try:
        # Scan /proc for process directories
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                try:
                    pid = int(entry)
                    cmdline = get_process_command(pid)

                    # Check if pattern matches
                    if command_pattern.lower() in cmdline.lower():
                        matching_pids.append({
                            "pid": pid,
                            "command": cmdline
                        })
                except:
                    continue
    except:
        pass

    return matching_pids


def sleep_until_command_complete(arguments):
    """Block until all processes matching a command pattern complete"""
    command_pattern = arguments.get("command_pattern")
    if not command_pattern:
        raise ValueError("command_pattern is required")

    timeout = arguments.get("timeout", 7200)
    poll_interval = arguments.get("poll_interval", 1.0)

    start_time = time.time()

    # Find initial matching processes
    initial_processes = find_processes_by_command(command_pattern)

    if not initial_processes:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "command_pattern": command_pattern,
                        "status": "not_found",
                        "message": f"No processes found matching pattern: {command_pattern}",
                        "start_time": datetime.now().isoformat()
                    }, indent=2)
                }
            ]
        }

    initial_pids = [p["pid"] for p in initial_processes]

    # Silent blocking loop
    while True:
        elapsed = time.time() - start_time

        # Check if any of the initial processes still exist
        still_running = [pid for pid in initial_pids if process_exists(pid)]

        if not still_running:
            # All processes completed!
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "command_pattern": command_pattern,
                            "status": "completed",
                            "initial_pids": initial_pids,
                            "process_count": len(initial_pids),
                            "elapsed_seconds": int(elapsed),
                            "end_time": datetime.now().isoformat(),
                            "message": f"All {len(initial_pids)} matching processes completed after {int(elapsed)} seconds"
                        }, indent=2)
                    }
                ]
            }

        # Check for timeout
        if elapsed >= timeout:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "command_pattern": command_pattern,
                            "status": "timeout",
                            "initial_pids": initial_pids,
                            "still_running_pids": still_running,
                            "completed_count": len(initial_pids) - len(still_running),
                            "still_running_count": len(still_running),
                            "timeout_seconds": timeout,
                            "elapsed_seconds": int(elapsed),
                            "end_time": datetime.now().isoformat(),
                            "message": f"Timeout after {timeout} seconds. {len(still_running)}/{len(initial_pids)} processes still running."
                        }, indent=2)
                    }
                ]
            }

        # Sleep before next check
        time.sleep(poll_interval)


def quick_check(arguments):
    """Quick non-blocking check if a process is running"""
    pid = arguments.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid PID")

    exists = process_exists(pid)
    command = get_process_command(pid) if exists else None

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "pid": pid,
                    "running": exists,
                    "command": command,
                    "checked_at": datetime.now().isoformat()
                }, indent=2)
            }
        ]
    }


def main():
    """Main MCP server loop"""
    while True:
        try:
            request = receive_message()
            if request is None:
                break

            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            try:
                if method == "initialize":
                    result = handle_initialize(params)
                elif method == "tools/list":
                    result = handle_tools_list()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = handle_tools_call(tool_name, arguments)
                else:
                    raise ValueError(f"Unknown method: {method}")

                # Send success response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                send_message(response)

            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                send_message(error_response)

        except KeyboardInterrupt:
            break
        except Exception:
            break


if __name__ == "__main__":
    main()
