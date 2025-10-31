#!/usr/bin/env python3
"""
Hook to block creation of all script files.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_script_creation(event):
    """Block creation of script files."""
    
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
    
    if path.suffix in script_extensions:
        return {
            'action': 'stop',
            'message': f"Script creation blocked: {path.name}. Scripts are not allowed."
        }
    
    # Check for shebang in content
    content = params.get('content', '')
    if content.startswith('#!'):
        return {
            'action': 'stop',
            'message': f"Script creation blocked: {path.name} contains shebang. Scripts are not allowed."
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_script_creation(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))