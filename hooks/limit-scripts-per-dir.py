#!/usr/bin/env python3
import json
import sys
import os

# Configuration - set MAX_SCRIPTS_PER_DIR as environment variable
# If not set or blank, no limit is enforced
MAX_SCRIPTS = os.environ.get('MAX_SCRIPTS_PER_DIR', '').strip()

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name in ["Write", "Edit", "MultiEdit"]:
    file_path = tool_input.get("file_path", "")
    
    if not file_path:
        sys.exit(0)
    
    # Skip if no limit configured
    if not MAX_SCRIPTS or not MAX_SCRIPTS.isdigit():
        sys.exit(0)
    
    max_limit = int(MAX_SCRIPTS)
    
    # Get directory and check if new file is a script
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # Common script extensions
    script_extensions = {
        '.py', '.sh', '.bash', '.zsh', '.fish', '.pl', '.rb', '.js', '.ts',
        '.php', '.go', '.rs', '.java', '.scala', '.kt', '.swift', '.r',
        '.R', '.m', '.lua', '.tcl', '.ps1', '.bat', '.cmd', '.vbs'
    }
    
    # Check if this file is a script
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in script_extensions:
        sys.exit(0)
    
    # Check if directory exists
    if not os.path.exists(directory):
        sys.exit(0)
    
    # Count existing script files
    script_count = 0
    existing_scripts = []
    
    for existing_file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, existing_file)):
            existing_ext = os.path.splitext(existing_file)[1].lower()
            if existing_ext in script_extensions:
                script_count += 1
                existing_scripts.append(existing_file)
    
    # Check if adding this file would exceed limit
    # (Don't count if we're editing an existing file)
    if not os.path.exists(file_path):
        script_count += 1
    
    if script_count > max_limit:
        print("SCRIPT LIMIT EXCEEDED!", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"Directory already has {len(existing_scripts)} script files", file=sys.stderr)
        print(f"Maximum allowed: {max_limit}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Existing scripts:", file=sys.stderr)
        for script in existing_scripts:
            print(f"  • {script}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Organize scripts into subdirectories or clean up unused files.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)