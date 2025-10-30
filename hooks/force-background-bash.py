#!/usr/bin/env python3
"""
Hook to force all bash commands to run in background (non-blocking).
This modifies the event to set run_in_background=true for all bash commands.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def force_background(event):
    """Force bash commands to run in background."""
    
    # Only modify Bash tool
    if event.get('tool') != 'Bash':
        return None
    
    params = event.get('params', {})
    
    # Force run_in_background to true
    if not params.get('run_in_background', False):
        # Modify the event to run in background
        event['params']['run_in_background'] = True
        
        # Return continue with modified event
        return {
            'action': 'continue',
            'modifiedEvent': event
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = force_background(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))