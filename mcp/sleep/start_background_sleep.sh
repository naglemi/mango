#!/bin/bash
# Start a sleep process in the background and return its PID

# Start sleep in background
sleep 5 &
PID=$!

echo "Started sleep 5 with PID: $PID"
echo "$PID" > /tmp/test_sleep_pid

# Don't wait for it - let it run independently
echo "Process running independently, will complete in 5 seconds"
