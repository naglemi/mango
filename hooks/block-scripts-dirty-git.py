#!/usr/bin/env python3
import json
import sys
import re
import subprocess

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Check for Python, R, or shell script execution
    script_patterns = [
        r'\bpython\s+.*\.py\b',
        r'\bpython3\s+.*\.py\b',
        r'\bRscript\s+.*\.R\b',
        r'\bR\s+.*\.R\b',
        r'\bbash\s+.*\.sh\b',
        r'\bsh\s+.*\.sh\b',
        r'\.\/.*\.py\b',
        r'\.\/.*\.R\b',
        r'\.\/.*\.sh\b'
    ]
    
    # Check if command matches script execution patterns
    is_script_execution = False
    for pattern in script_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            is_script_execution = True
            break
    
    if is_script_execution:
        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            print("SCRIPT EXECUTION BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Cannot execute scripts when git working directory is dirty.", file=sys.stderr)
            print("Commit or stash your changes first.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Dirty files:", file=sys.stderr)
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}", file=sys.stderr)
            sys.exit(2)

sys.exit(0)