#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block piping to head or tail
    pipe_patterns = [
        r'\|\s*head\b',
        r'\|\s*tail\b'
    ]
    
    for pattern in pipe_patterns:
        if re.search(pattern, command):
            print("HEAD/TAIL PIPING BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Piping to head or tail is forbidden.", file=sys.stderr)
            print("Use proper tools to view complete output.", file=sys.stderr)
            sys.exit(2)

sys.exit(0)