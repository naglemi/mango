#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block error hiding patterns
    error_hiding_patterns = [
        r'2>/dev/null',
        r'2> */dev/null',
        r'>/dev/null 2>&1',
        r'> */dev/null 2>&1',
        r'&>/dev/null',
        r'&> */dev/null'
    ]
    
    for pattern in error_hiding_patterns:
        if re.search(pattern, command):
            print("ERROR HIDING BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Redirecting errors to /dev/null is forbidden.", file=sys.stderr)
            print("Errors must be visible for debugging.", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Blocked pattern: {pattern}", file=sys.stderr)
            sys.exit(2)

sys.exit(0)