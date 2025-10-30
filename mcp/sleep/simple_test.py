#!/usr/bin/env python3
"""
Simple direct test of sleep MCP logic
"""

import subprocess
import time
import json

# Start test process
print("Starting test process: sleep 3")
test_proc = subprocess.Popen(["sleep", "3"])
test_pid = test_proc.pid
print(f"PID: {test_pid}")

# Manually call the MCP server with JSON-RPC
mcp_server = subprocess.Popen(
    ["python3", "/home/ubuntu/mango/mcp/sleep/sleep_mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Initialize
print("\n1. Initializing MCP...")
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
}
mcp_server.stdin.write((json.dumps(init_request) + "\n").encode())
mcp_server.stdin.flush()
response = mcp_server.stdout.readline()
print(f"   Response: {json.loads(response)['result']['serverInfo']['name']}")

# Call sleep_until_complete
print(f"\n2. Calling sleep_until_complete for PID {test_pid}...")
print("   (This should block for ~3 seconds)")
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

print("   Waiting for response...")
response_line = mcp_server.stdout.readline()
elapsed = time.time() - start_time

print(f"   Got response after {elapsed:.2f} seconds")

response = json.loads(response_line)
if "result" in response:
    result = response["result"]
    content = json.loads(result["content"][0]["text"])
    print(f"   Status: {content['status']}")
    print(f"   Message: {content.get('message', 'N/A')}")
    print(f"   Full result: {json.dumps(content, indent=2)}")
else:
    print(f"   Error: {response.get('error', 'Unknown error')}")

# Clean up
mcp_server.terminate()
test_proc.wait()

print("\n Test complete")
