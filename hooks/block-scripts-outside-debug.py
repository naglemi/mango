#!/usr/bin/env python3
"""
Hook to block script creation outside of debugging_scripts folder.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_script_location(event):
    """Block script creation outside debugging_scripts folder."""
    
    # Only check Write operations (new files)
    if event.get('tool') != 'Write':
        return None
    
    params = event.get('params', {})
    file_path = params.get('file_path', '')
    
    if not file_path:
        return None
    
    # Check if it's a script file
    path = Path(file_path)
    
    # Script extensions
    script_extensions = {'.py', '.sh', '.bash', '.js', '.ts', '.rb', '.pl', '.php', '.go', '.rs', '.lua', '.r', '.R'}
    
    is_script = False
    
    # Check extension
    if path.suffix in script_extensions:
        is_script = True
    
    # Check for shebang in content
    content = params.get('content', '')
    if content.startswith('#!'):
        is_script = True
    
    if is_script:
        # Check if it's in debugging_scripts folder
        path_parts = path.parts
        if 'debugging_scripts' not in path_parts:
            return {
                'action': 'stop',
                'message': f"Script creation blocked: {path.name} must be created in a 'debugging_scripts' folder."
            }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_script_location(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))