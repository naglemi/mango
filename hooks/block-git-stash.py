#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block git stash operations
    if re.search(r'\bgit\s+stash\b', command, re.IGNORECASE):
        print("GIT STASH BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print("git stash is forbidden in this workspace.", file=sys.stderr)
        print("Use proper branching and commits instead.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)