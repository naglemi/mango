#!/usr/bin/env python3
import os
import sys
import subprocess

print(f"TMUX env var: {os.environ.get('TMUX', 'NOT SET')}")
print(f"Current working directory: {os.getcwd()}")

# Check tmux capture-pane
try:
    result = subprocess.run(
        ['tmux', 'capture-pane', '-S', '-', '-p'],
        capture_output=True, text=True, check=True
    )
    print(f"Buffer content length: {len(result.stdout)} characters")
    lines = result.stdout.split('\n')
    print(f"Buffer lines: {len(lines)}")
    print("First 3 lines:")
    for i, line in enumerate(lines[:3]):
        print(f"  {i+1}: {repr(line)}")

    # Copy first line to clipboard to see what happens
    if lines:
        first_line = lines[0] if lines[0].strip() else lines[1] if len(lines) > 1 else "empty"
        print(f"Copying to clipboard: {repr(first_line)}")
        subprocess.run(['xclip', '-selection', 'clipboard'], input=first_line, text=True, check=True)
        print(" Successfully copied to clipboard")

except Exception as e:
    print(f"Error: {e}")

input("Press Enter to continue...")