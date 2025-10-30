#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block sed, awk, and other inline editing tools
    editing_patterns = [
        r'\bsed\s+',
        r'\bawk\s+',
        r'\bperl\s+-[pnie]',
        r'\bperl\s+.*-[pnie]'
    ]
    
    for pattern in editing_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print("INLINE EDITING BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Using sed, awk, or inline editing tools is forbidden.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Instead, you must:", file=sys.stderr)
            print("1. Read the file using Read tool", file=sys.stderr)
            print("2. Use Edit or MultiEdit tools for modifications", file=sys.stderr)
            print("3. Make explicit, reviewable changes", file=sys.stderr)
            print("", file=sys.stderr)
            print("Inline editing tools hide what changes are being made.", file=sys.stderr)
            sys.exit(2)

sys.exit(0)