#!/usr/bin/env python3
"""
Hook to force all bash commands to run in foreground (blocking background execution).
This prevents agents from using run_in_background parameter.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def force_foreground(event):
    """Force bash commands to run in foreground."""
    
    # Only check Bash tool
    if event.get('tool') != 'Bash':
        return None
    
    params = event.get('params', {})
    
    # Check if run_in_background is set to true
    if params.get('run_in_background', False):
        return {
            'action': 'stop',
            'message': 'Background execution blocked. All commands must run in foreground.'
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = force_foreground(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))