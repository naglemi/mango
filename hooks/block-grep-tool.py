#!/usr/bin/env python3
"""
Hook to block the Grep tool - no blind content searching!
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

def check_grep_tool(event):
    """Block Grep tool usage."""
    
    if event.get('tool') == 'Grep':
        default_msg = "NO content searching! Read ENTIRE files, understand the code, trace through logic manually."
        return {
            'action': 'stop',
            'message': get_custom_message('block-grep-tool', default_msg)
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_grep_tool(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))