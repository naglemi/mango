#!/usr/bin/env python3
import json
import sys
import subprocess
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Check for Python script execution
    python_patterns = [
        r'\bpython\s+.*\.py\b',
        r'\bpython3\s+.*\.py\b',
        r'\.\/.*\.py\b'
    ]
    
    is_python_execution = False
    python_file = None
    
    for pattern in python_patterns:
        match = re.search(pattern, command)
        if match:
            is_python_execution = True
            # Extract the .py file name
            py_match = re.search(r'(\S*\.py)', command)
            if py_match:
                python_file = py_match.group(1)
            break
    
    if is_python_execution and python_file:
        # Check if the Python file exists and has syntax errors
        result = subprocess.run(
            ['python3', '-m', 'py_compile', python_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("PYTHON SYNTAX ERROR!", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Cannot run {python_file} - syntax errors found:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(2)

sys.exit(0)