#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")

    # Block cd commands
    if re.search(r'\bcd\s+', command):
        print("CD COMMAND BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Use absolute paths instead of changing directories.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
