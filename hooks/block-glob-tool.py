#!/usr/bin/env python3
"""
Hook to block the Glob tool - no blind pattern searching!
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

def check_glob_tool(event):
    """Block Glob tool usage."""
    
    if event.get('tool') == 'Glob':
        default_msg = "NO pattern searching! Read files directly, navigate with cd/ls, follow logic not patterns."
        return {
            'action': 'stop',
            'message': get_custom_message('block-glob-tool', default_msg)
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_glob_tool(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))