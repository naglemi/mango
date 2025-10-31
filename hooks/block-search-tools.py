#!/usr/bin/env python3
import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block search tools
    search_patterns = [
        r'\bfind\s+',
        r'\bgrep\s+',
        r'\brg\s+',
        r'\bripgrep\s+',
        r'\bag\s+',
        r'\back\s+',
        r'\bsilver-searcher\s+'
    ]
    
    for pattern in search_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print("SEARCH TOOLS BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Using find, grep, or similar search tools is forbidden.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Instead, you must:", file=sys.stderr)
            print("1. Read entire scripts into context using Read tool", file=sys.stderr)
            print("2. Walk from script to script using logic and reasoning", file=sys.stderr)
            print("3. Use chain-of-thought to trace through the codebase", file=sys.stderr)
            print("4. Follow imports, function calls, and data flow manually", file=sys.stderr)
            print("", file=sys.stderr)
            print("This approach is more thorough and intelligent than grep.", file=sys.stderr)
            sys.exit(2)

sys.exit(0)