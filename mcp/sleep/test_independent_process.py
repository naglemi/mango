#!/usr/bin/env python3
"""
Test MCP with an independently started process
"""

import json
import subprocess
import time

# Read the PID of the independently started process
with open("/tmp/test_sleep_pid", "r") as f:
    test_pid = int(f.read().strip())

print(f"Testing with independently started process PID: {test_pid}")

# Start MCP server
mcp_server = subprocess.Popen(
    ["python3", "/home/ubuntu/mango/mcp/sleep/debug_sleep_mcp.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Initialize
init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
mcp_server.stdin.write((json.dumps(init_request) + "\n").encode())
mcp_server.stdin.flush()
_ = mcp_server.stdout.readline()

# Call sleep_until_complete
print(f"Calling sleep_until_complete (should complete in ~5 seconds)...")
start_time = time.time()

call_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "sleep_until_complete",
        "arguments": {"pid": test_pid, "timeout": 10, "poll_interval": 0.5}
    }
}
mcp_server.stdin.write((json.dumps(call_request) + "\n").encode())
mcp_server.stdin.flush()

response_line = mcp_server.stdout.readline()
elapsed = time.time() - start_time

print(f"Got response after {elapsed:.2f} seconds")

response = json.loads(response_line)
content = json.loads(response["result"]["content"][0]["text"])
print(f"Status: {content['status']}")
print(f"Iterations: {content.get('iterations', 'N/A')}")

# Get debug output
mcp_server.terminate()
_, stderr = mcp_server.communicate(timeout=2)

print("\n" + "=" * 60)
print("DEBUG OUTPUT:")
print("=" * 60)
for line in stderr.decode().split('\n')[-15:]:  # Last 15 lines
    print(line)

print("\n Test complete")
