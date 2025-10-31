#!/usr/bin/env python3
"""
Claude Code hook to block mkdir and mv commands.

This enforces the rule that:
1. No new directories can be created
2. No files can be moved
3. Files stay where they are originally output

This ensures reproducibility and prevents confusion about file locations.
"""

import json
import sys

# Read the tool input from stdin
data = json.load(sys.stdin)

# Get the command from the Bash tool input
command = data.get('tool_input', {}).get('command', '')

# List of forbidden commands/patterns
forbidden_patterns = [
    'mkdir',
    'mv ',  # Note the space to avoid blocking 'remove' etc
    'cp -r',  # Also block recursive copy which could create directories
]

# Check if any forbidden pattern is in the command
for pattern in forbidden_patterns:
    if pattern in command:
        # Exit with code 2 to block the command
        print(f"BLOCKED: '{pattern}' command is not allowed!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Project rules:", file=sys.stderr)
        print("  - No new directories can be created", file=sys.stderr)
        print("  - No files can be moved after creation", file=sys.stderr)
        print("  - Files must stay in their original output locations", file=sys.stderr)
        print("", file=sys.stderr)
        print("This ensures reproducibility and prevents confusion.", file=sys.stderr)
        sys.exit(2)

# If no forbidden patterns found, allow the command
sys.exit(0)