#!/usr/bin/env python3
import json
import sys
import re

FORBIDDEN_PATTERNS = [
    r'\btry\s*:',
    r'\bexcept\s+\w+',
    r'\bexcept\s*:',
    r'\bexcept\s*\(',
    r'\.catch\s*\(',
    r'\.then\s*\(',
    r'\.finally\s*\(',
    r'\bcatch\s*\(',
    r'\brescue\s+',
    r'\berror\s*\(',
    r'on\s+error\s+',
    r'if\s+err\s*!=\s*nil',
    r'if\s+error\s*!=\s*nil',
    r'errors\.New\(',
    r'fmt\.Errorf\(',
    r'panic\(',
    r'recover\(',
]

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name in ["Write", "Edit", "MultiEdit"]:
    content = ""
    
    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        content = " ".join([e.get("new_string", "") for e in edits])
    
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            print("ERROR HANDLING DETECTED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Error handling is strictly forbidden in this codebase.", file=sys.stderr)
            print("Write linear code that fails fast instead.", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Detected pattern: {pattern}", file=sys.stderr)
            sys.exit(2)

sys.exit(0)