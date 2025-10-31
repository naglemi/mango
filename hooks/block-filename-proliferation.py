#!/usr/bin/env python3
import json
import sys
import os
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name in ["Write", "Edit", "MultiEdit"]:
    file_path = tool_input.get("file_path", "")
    
    if not file_path:
        sys.exit(0)
    
    # Get directory and filename
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # Extract first word before first delimiter (_ or -)
    def get_first_word(name):
        # Split on _ or - and take the first part
        match = re.split(r'[_-]', name)
        return match[0] if match else name
    
    new_first_word = get_first_word(filename)
    
    # Check if directory exists
    if not os.path.exists(directory):
        sys.exit(0)
    
    # Check existing files in the same directory
    existing_files = []
    for existing_file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, existing_file)):
            existing_first_word = get_first_word(existing_file)
            if existing_first_word.lower() == new_first_word.lower() and existing_file != filename:
                existing_files.append(existing_file)
    
    if existing_files:
        print("FILENAME PROLIFERATION BLOCKED!", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Cannot create '{filename}' - first word '{new_first_word}' already exists", file=sys.stderr)
        print("", file=sys.stderr)
        print("Conflicting files in directory:", file=sys.stderr)
        for existing in existing_files:
            print(f"  • {existing}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Choose a different base name to avoid filename proliferation.", file=sys.stderr)
        print("This prevents ending up with: script.py, script_v2.py, script_final.py", file=sys.stderr)
        sys.exit(2)

sys.exit(0)