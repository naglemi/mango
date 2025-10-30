#!/usr/bin/env python3
"""
Claude Code hook to block dangerous git commands that could add massive amounts of raw data.
This prevents accidental staging of GB of genomic data files.
"""

import json
import sys
import re

# Load input from stdin
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

# Only check Bash commands
if tool_name != "Bash":
    sys.exit(0)

# List of dangerous git patterns
DANGEROUS_PATTERNS = [
    (r'\bgit\s+add\s+-A\b', "git add -A is FORBIDDEN! Use git add <specific_file> instead."),
    (r'\bgit\s+add\s+\.\s*($|[;&|])', "git add . is FORBIDDEN! Use git add <specific_file> instead."),
    (r'\bgit\s+add\s+-u\b', "git add -u is FORBIDDEN! Use git add <specific_file> instead."),
    (r'\bgit\s+add\s+--all\b', "git add --all is FORBIDDEN! Use git add <specific_file> instead."),
    (r'\bgit\s+add\s+--update\b', "git add --update is FORBIDDEN! Use git add <specific_file> instead."),
    (r'\bgit\s+add\s+\*', "git add with wildcards is FORBIDDEN! Use git add <specific_file> instead."),
]

# Check command against dangerous patterns
for pattern, message in DANGEROUS_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        print(f"BLOCKED: {message}", file=sys.stderr)
        print("This workspace contains many GB of raw genomic data files.", file=sys.stderr)
        print("Always add files one at a time to avoid staging massive datasets.", file=sys.stderr)
        print("Example: git add Figure4.png", file=sys.stderr)
        # Exit code 2 blocks the tool call
        sys.exit(2)

# Allow safe commands
sys.exit(0)