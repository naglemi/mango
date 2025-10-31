#\!/usr/bin/env python3
"""
Hook to enforce sequential numbering of scripts (01_, 02_, 03_, etc.)
Blocks creation of scripts that don't follow sequential ordering.
"""

import sys
import json
import os
import re
from pathlib import Path

def check_sequential_scripts(tool_data):
    """Check if script creation follows sequential numbering."""
    tool_name = tool_data.get("name", "")
    
    # Only check Write, MultiEdit, and Edit tools for script creation
    if tool_name not in ["Write", "MultiEdit", "Edit"]:
        return None
    
    # Get the file path
    if tool_name == "Write":
        file_path = tool_data.get("parameters", {}).get("file_path", "")
    elif tool_name == "Edit":
        file_path = tool_data.get("parameters", {}).get("file_path", "")
    elif tool_name == "MultiEdit":
        file_path = tool_data.get("parameters", {}).get("file_path", "")
    else:
        return None
    
    # Check if it's a Python or shell script
    if not (file_path.endswith('.py') or file_path.endswith('.sh')):
        return None
    
    # Extract directory and filename
    file_path_obj = Path(file_path)
    directory = file_path_obj.parent
    filename = file_path_obj.name
    
    # Check if filename starts with a number pattern
    if not re.match(r'^\d{2}_', filename):
        # If no number prefix, check if directory has numbered scripts
        if directory.exists():
            numbered_scripts = []
            for f in directory.iterdir():
                if f.is_file() and (f.suffix in ['.py', '.sh']):
                    if re.match(r'^\d{2}_', f.name):
                        numbered_scripts.append(f.name)
            
            if numbered_scripts:
                # Directory has numbered scripts, new script must be numbered
                numbered_scripts.sort()
                last_num = int(numbered_scripts[-1][:2])
                next_num = last_num + 1
                return {
                    "action": "block",
                    "message": f" SEQUENTIAL NUMBERING REQUIRED\!\n\nThis directory contains numbered scripts. New script MUST be numbered.\nExisting scripts: {', '.join(numbered_scripts)}\nYour script should be named: {next_num:02d}_{filename}\n\nFix the filename to follow sequential ordering\!"
                }
        return None  # No numbered scripts in directory, allow unnumbered
    
    # Script has number prefix, verify it's sequential
    script_num = int(filename[:2])
    
    # Check existing scripts in directory
    if not directory.exists():
        # New directory, first script must be 01_
        if script_num \!= 1:
            return {
                "action": "block",
                "message": f" SEQUENTIAL VIOLATION\!\n\nFirst script in new directory MUST start with 01_\nYou tried to create: {filename}\nCorrect name: 01_{filename[3:]}"
            }
        return None
    
    # Get all numbered scripts in directory
    existing_numbers = []
    existing_scripts = []
    for f in directory.iterdir():
        if f.is_file() and (f.suffix in ['.py', '.sh']):
            match = re.match(r'^(\d{2})_', f.name)
            if match:
                num = int(match.group(1))
                # Skip if this is an edit to existing file
                if f.name == filename and tool_name in ["Edit", "MultiEdit"]:
                    continue
                existing_numbers.append(num)
                existing_scripts.append(f.name)
    
    existing_numbers.sort()
    existing_scripts.sort()
    
    # Check for sequential ordering
    if not existing_numbers:
        # First numbered script must be 01
        if script_num \!= 1:
            return {
                "action": "block",
                "message": f" SEQUENTIAL VIOLATION\!\n\nFirst numbered script MUST be 01_\nYou tried: {filename}\nCorrect: 01_{filename[3:]}"
            }
    else:
        # Check for gaps in sequence
        expected_sequence = list(range(1, max(existing_numbers) + 1))
        current_sequence = existing_numbers.copy()
        
        # If creating new script, it should be next in sequence
        if tool_name == "Write" or (tool_name in ["Edit", "MultiEdit"] and not Path(file_path).exists()):
            next_expected = max(existing_numbers) + 1
            if script_num \!= next_expected:
                # Check if filling a gap
                if script_num in expected_sequence and script_num not in current_sequence:
                    return None  # Filling a gap is allowed
                else:
                    return {
                        "action": "block", 
                        "message": f" SEQUENTIAL VIOLATION\!\n\nExisting scripts: {', '.join(existing_scripts)}\nNext script MUST be numbered: {next_expected:02d}_\nYou tried: {filename}\n\nSTRICT SEQUENTIAL ORDERING REQUIRED\!"
                    }
        
        # Check if number already exists (duplicate)
        if script_num in existing_numbers:
            conflicting = [f for f in existing_scripts if f.startswith(f"{script_num:02d}_")]
            return {
                "action": "block",
                "message": f" DUPLICATE NUMBER\!\n\nScript with number {script_num:02d}_ already exists: {conflicting[0]}\nUse the next available number: {max(existing_numbers) + 1:02d}_"
            }
    
    return None

def main():
    # Read the event from stdin
    event_data = json.loads(sys.stdin.read())
    
    # Check if this is a PreToolUse event
    if event_data.get("event") \!= "PreToolUse":
        sys.exit(0)
    
    # Check the tool data
    tool_data = event_data.get("data", {})
    result = check_sequential_scripts(tool_data)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    # Allow the action
    sys.exit(0)

if __name__ == "__main__":
    main()
