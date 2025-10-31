#!/usr/bin/env python3
"""
Debug test for sleep MCP
"""

import subprocess
import time
import os

# Start a test process
print("Starting test process: sleep 5")
test_proc = subprocess.Popen(["sleep", "5"])
test_pid = test_proc.pid
print(f"Test PID: {test_pid}")

# Check if process exists
print(f"\nChecking if PID {test_pid} exists...")
try:
    os.kill(test_pid, 0)
    print(" Process exists (via os.kill(pid, 0))")
except ProcessLookupError:
    print(" Process not found (ProcessLookupError)")
except PermissionError:
    print(" Process exists but permission denied")

# Read command
try:
    with open(f"/proc/{test_pid}/cmdline", 'r') as f:
        cmdline = f.read().replace('\x00', ' ').strip()
        print(f" Command: {cmdline}")
except Exception as e:
    print(f" Could not read command: {e}")

# Wait a bit
print("\nWaiting 2 seconds...")
time.sleep(2)

# Check again
try:
    os.kill(test_pid, 0)
    print(" Process still exists")
except ProcessLookupError:
    print(" Process no longer exists")

# Wait for process to complete
print("\nWaiting for process to complete naturally...")
test_proc.wait()
print(f" Process completed with return code: {test_proc.returncode}")

# Check again
try:
    os.kill(test_pid, 0)
    print(" Process still exists (shouldn't happen!)")
except ProcessLookupError:
    print(" Process no longer exists (expected)")
