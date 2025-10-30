#!/usr/bin/env python3
"""
Debug version of sleep MCP server with verbose output
"""

import json
import sys
import os
import time
from datetime import datetime


def send_message(message):
    """Send a JSON-RPC message to stdout"""
    print(json.dumps(message), file=sys.stdout)
    sys.stdout.flush()


def log_debug(msg):
    """Log debug message to stderr"""
    print(f"[DEBUG] {msg}", file=sys.stderr)
    sys.stderr.flush()


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


def sleep_until_complete_debug(arguments):
    """Block until a specific PID completes - DEBUG VERSION"""
    pid = arguments.get("pid")
    timeout = arguments.get("timeout", 7200)
    poll_interval = arguments.get("poll_interval", 1.0)

    start_time = time.time()

    log_debug(f"Starting sleep_until_complete for PID {pid}")
    log_debug(f"Timeout: {timeout}s, Poll interval: {poll_interval}s")

    # Check if process exists at start
    if not process_exists(pid):
        log_debug(f"PID {pid} not found at start")
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "pid": pid,
                        "status": "not_found",
                        "message": f"Process {pid} not found or already exited"
                    }, indent=2)
                }
            ]
        }

    log_debug(f"PID {pid} exists at start, entering poll loop")

    # Poll loop with debug output
    iteration = 0
    while True:
        iteration += 1
        elapsed = time.time() - start_time

        # Check if process still exists
        still_exists = process_exists(pid)
        log_debug(f"Iteration {iteration}: elapsed={elapsed:.2f}s, process_exists={still_exists}")

        if not still_exists:
            log_debug(f"Process {pid} no longer exists! Returning completed status")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "pid": pid,
                            "status": "completed",
                            "elapsed_seconds": int(elapsed),
                            "iterations": iteration,
                            "message": f"Process {pid} completed after {int(elapsed)} seconds"
                        }, indent=2)
                    }
                ]
            }

        # Check for timeout
        if elapsed >= timeout:
            log_debug(f"Timeout reached after {elapsed:.2f}s")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "pid": pid,
                            "status": "timeout",
                            "timeout_seconds": timeout,
                            "elapsed_seconds": int(elapsed),
                            "iterations": iteration,
                            "still_running": True,
                            "message": f"Timeout reached after {timeout} seconds. Process {pid} still running."
                        }, indent=2)
                    }
                ]
            }

        # Sleep before next check
        log_debug(f"Sleeping for {poll_interval}s...")
        time.sleep(poll_interval)


def main():
    """Main MCP server loop"""
    log_debug("Starting debug sleep MCP server")

    while True:
        try:
            request = receive_message()
            if request is None:
                log_debug("No more input, exiting")
                break

            method = request.get("method")
            request_id = request.get("id")
            log_debug(f"Received request: method={method}, id={request_id}")

            try:
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "sleep-debug", "version": "1.0.0-debug"}
                    }
                elif method == "tools/call":
                    tool_name = request["params"]["name"]
                    arguments = request["params"].get("arguments", {})
                    log_debug(f"Calling tool: {tool_name}")
                    result = sleep_until_complete_debug(arguments)
                else:
                    raise ValueError(f"Unknown method: {method}")

                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                send_message(response)

            except Exception as e:
                log_debug(f"Error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                }
                send_message(error_response)

        except KeyboardInterrupt:
            log_debug("Keyboard interrupt")
            break
        except Exception as e:
            log_debug(f"Unexpected error: {e}")
            break

    log_debug("Server exiting")


if __name__ == "__main__":
    main()
