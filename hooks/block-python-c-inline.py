#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block python -c commands
    if re.search(r'\bpython[3]?\s+-c\b', command, re.IGNORECASE):
        print("PYTHON -c BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Inline Python scripts are forbidden for replicability.", file=sys.stderr)
        print("Create a proper .py file instead.", file=sys.stderr)
        print("Consider fixing/debugging existing scripts rather than creating new ones.", file=sys.stderr)
        sys.exit(2)
    
    # Block R -e commands
    if re.search(r'\bR\s+-e\b', command, re.IGNORECASE):
        print("R -e BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Inline R scripts are forbidden for replicability.", file=sys.stderr)
        print("Create a proper .R file instead.", file=sys.stderr)
        print("Consider fixing/debugging existing scripts rather than creating new ones.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
