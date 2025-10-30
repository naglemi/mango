#!/usr/bin/env python3
import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name == "Bash":
    command = tool_input.get("command", "")
    
    # Block hook management tools and files
    hook_patterns = [
        r'\bhook_manager\.py\b',
        r'\bhook_selector\.py\b',
        r'\bhook_installer\.py\b',
        r'\.claude/settings\.json',
        r'~/\.claude/settings\.json',
        r'/\.claude/settings\.json',
        r'hooks/.*\.py',
        r'hooks/.*\.sh'
    ]
    
    for pattern in hook_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print("HOOK SYSTEM TAMPERING BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Modifying hooks, hook scripts, or settings is forbidden.", file=sys.stderr)
            print("Agents cannot disable or circumvent their own restrictions.", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Blocked pattern: {pattern}", file=sys.stderr)
            sys.exit(2)

if tool_name in ["Write", "Edit", "MultiEdit"]:
    file_path = tool_input.get("file_path", "")
    
    # Block editing of hook files and settings
    forbidden_paths = [
        r'\.claude/settings\.json',
        r'hooks/.*\.py',
        r'hooks/.*\.sh',
        r'hook_manager\.py',
        r'hook_selector\.py',
        r'hook_installer\.py'
    ]
    
    for pattern in forbidden_paths:
        if re.search(pattern, file_path, re.IGNORECASE):
            print("HOOK FILE EDITING BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Editing hook files or settings is forbidden.", file=sys.stderr)
            print("Agents cannot modify their own constraints.", file=sys.stderr)
            sys.exit(2)

sys.exit(0)