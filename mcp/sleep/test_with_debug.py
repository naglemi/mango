#!/usr/bin/env python3
"""
Test with debug MCP server
"""

import subprocess
import time
import json

# Start test process
print("Starting test process: sleep 3")
test_proc = subprocess.Popen(["sleep", "3"])
test_pid = test_proc.pid
print(f"PID: {test_pid}")

# Start debug MCP server
print("\nStarting debug MCP server...")
mcp_server = subprocess.Popen(
    ["python3", "/home/ubuntu/mango/mcp/sleep/debug_sleep_mcp.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Initialize
print("\nInitializing...")
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
}
mcp_server.stdin.write((json.dumps(init_request) + "\n").encode())
mcp_server.stdin.flush()
response = mcp_server.stdout.readline()

# Call sleep_until_complete
print(f"\nCalling sleep_until_complete for PID {test_pid}...")
start_time = time.time()

call_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "sleep_until_complete",
        "arguments": {
            "pid": test_pid,
            "timeout": 10,
            "poll_interval": 0.5
        }
    }
}
mcp_server.stdin.write((json.dumps(call_request) + "\n").encode())
mcp_server.stdin.flush()

print("Waiting for response...")

# Read response
response_line = mcp_server.stdout.readline()
elapsed = time.time() - start_time

print(f"\n Got response after {elapsed:.2f} seconds")

response = json.loads(response_line)
if "result" in response:
    result = response["result"]
    content = json.loads(result["content"][0]["text"])
    print(f"Status: {content['status']}")
    print(f"Iterations: {content.get('iterations', 'N/A')}")
    print(f"Message: {content.get('message', 'N/A')}")
else:
    print(f"Error: {response.get('error', 'Unknown')}")

# Clean up and get stderr
print("\nCleaning up...")
mcp_server.terminate()
_, stderr = mcp_server.communicate(timeout=2)

print("\n" + "=" * 60)
print("DEBUG OUTPUT from MCP server:")
print("=" * 60)
print(stderr.decode())

test_proc.wait()
print(" Test complete")
