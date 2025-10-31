#!/usr/bin/env python3
"""
Claude Code hook to block creation of files with version suffixes.

This prevents the proliferation of files like:
- something_FINAL.py
- something_ACTUAL.py
- something_fixed.py
- something_revised.py
- something_complete.py
- something_actuallycomplete.py
- something_v2.py
- something_corrected.py

We use Git for versioning. Overwrite files instead of creating new versions.
"""

import json
import sys
import re

# Read the tool input from stdin
data = json.load(sys.stdin)

# Get the tool name and input
tool_name = data.get('tool_name', '')
tool_input = data.get('tool_input', {})

# Check if this is a file creation/writing tool
if tool_name in ['Write', 'Edit', 'MultiEdit']:
    file_path = tool_input.get('file_path', '')
    
    # List of forbidden patterns in filenames
    forbidden_patterns = [
        r'_FINAL',
        r'_ACTUAL', 
        r'_fixed',
        r'_revised',
        # r'_complete',  # Allowing _complete for figure scripts
        r'_actuallycomplete',
        r'_corrected',
        r'_new',
        r'_old',
        r'_backup',
        r'_v\d+',  # _v2, _v3, etc
        r'_version\d+',
        r'_draft',
        r'_temp',
        r'_tmp',
        r'FINAL_',
        r'ACTUAL_',
        r'CORRECTED_',
        r'COMPREHENSIVE_',
        r'SYSTEMATIC_'
    ]
    
    # Check if filename contains any forbidden pattern
    for pattern in forbidden_patterns:
        if re.search(pattern, file_path, re.IGNORECASE):
            print(f"BLOCKED: File versioning suffix '{pattern}' not allowed!", file=sys.stderr)
            print("", file=sys.stderr)
            print("DO NOT create multiple versions of files!", file=sys.stderr)
            print("", file=sys.stderr)
            print("Instead:", file=sys.stderr)
            print("  - Overwrite the existing file", file=sys.stderr)
            print("  - Use git for version control", file=sys.stderr)
            print("  - Delete old attempts instead of keeping them", file=sys.stderr)
            print("", file=sys.stderr)
            print("We don't want:", file=sys.stderr)
            print("  script.py", file=sys.stderr)
            print("  script_fixed.py", file=sys.stderr)
            print("  script_fixed_FINAL.py", file=sys.stderr)
            print("  script_ACTUALLY_FINAL_v2.py", file=sys.stderr)
            print("", file=sys.stderr)
            print("Just use: script.py and let git track changes!", file=sys.stderr)
            sys.exit(2)

# Allow the operation
sys.exit(0)