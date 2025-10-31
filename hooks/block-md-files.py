#!/usr/bin/env python3
"""
Hook to block creation/editing of MD files except:
- README.md in root or subdirectories
- Any .md files in hidden folders (starting with .)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

def check_md_file(event):
    """Block MD file creation/editing with exceptions."""
    
    # Check Write, Edit, and MultiEdit operations
    if event.get('tool') not in ['Write', 'Edit', 'MultiEdit']:
        return None
    
    params = event.get('params', {})
    file_path = params.get('file_path', '')
    
    if not file_path:
        return None
    
    path = Path(file_path)
    
    # Only check .md files
    if path.suffix.lower() != '.md':
        return None
    
    # Allow README.md anywhere
    if path.name == 'README.md':
        return None
    
    # Check if file is in a hidden folder (folder starting with .)
    for part in path.parts:
        if part.startswith('.') and part != '.':
            # File is in a hidden folder, allow it
            return None
    
    # Block all other .md files
    default_msg = f"Markdown file blocked: {path.name}. Only README.md or .md files in hidden folders are allowed."
    return {
        'action': 'stop',
        'message': get_custom_message('block-md-files', default_msg)
    }

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_md_file(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))