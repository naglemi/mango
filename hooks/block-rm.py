#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block rm commands
    if re.search(r'\brm\s+', command, re.IGNORECASE):
        print("RM COMMAND BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print("rm command is forbidden for safety.", file=sys.stderr)
        print("Use file manager or specific file operations instead.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)