#!/usr/bin/env python3
import json
import sys
import re
import os

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name in ["Write", "Edit", "MultiEdit"]:
    file_path = tool_input.get("file_path", "")
    
    if not file_path:
        sys.exit(0)
    
    # Get just the filename
    filename = os.path.basename(file_path)
    
    # FORBIDDEN WORDS - blocks version-like naming
    forbidden_words = [
        "final", "complete", "fixed", "revised", "resolved", "corrected", 
        "updated", "new", "old", "backup", "temp", "test", "debug", 
        "draft", "WIP", "todo", "shit", "fuck", "damn", "stupid", 
        "bad", "broken", "working", "good", "better", "best", 
        "real", "actual", "proper", "right", "wrong", "true", "false"
    ]
    
    # Check for forbidden words (case-insensitive)
    for word in forbidden_words:
        if re.search(rf'\b{word}\b', filename, re.IGNORECASE):
            print("BAD FILENAME BLOCKED!", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"File name '{filename}' contains forbidden word: '{word}'", file=sys.stderr)
            print("", file=sys.stderr)
            print("Forbidden patterns include:", file=sys.stderr)
            print("  • Version words (final, fixed, updated, new, old)", file=sys.stderr)
            print("  • Quality words (good, bad, better, broken)", file=sys.stderr)
            print("  • Status words (temp, backup, draft, WIP)", file=sys.stderr)
            print("  • Profanity and negative words", file=sys.stderr)
            print("", file=sys.stderr)
            print("Use git versioning instead of filename versioning!", file=sys.stderr)
            sys.exit(2)

sys.exit(0)