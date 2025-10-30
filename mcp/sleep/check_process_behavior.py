#!/usr/bin/env python3
"""
Check if the sleep process is actually completing
"""

import subprocess
import time
import os

# Start sleep process
print("Starting: sleep 3")
proc = subprocess.Popen(["sleep", "3"])
pid = proc.pid
print(f"PID: {pid}")

# Monitor it directly
for i in range(15):
    time.sleep(0.5)
    elapsed = i * 0.5

    # Check with os.kill
    try:
        os.kill(pid, 0)
        exists_via_kill = True
    except ProcessLookupError:
        exists_via_kill = False

    # Check with poll
    poll_result = proc.poll()

    print(f"  {elapsed:.1f}s: os.kill says exists={exists_via_kill}, poll={poll_result}")

    if not exists_via_kill and poll_result is not None:
        print(f" Process completed at {elapsed:.1f}s")
        break

print("\n Test complete")
