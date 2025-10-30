#!/usr/bin/env python3
"""
Hook to block the Search tool - no blind searching!
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

def check_search_tool(event):
    """Block Search tool usage."""
    
    if event.get('tool') == 'Search':
        default_msg = "NO searching! Navigate with cd/ls, read ENTIRE files, trace through imports and logic. THINK, don't search!"
        return {
            'action': 'stop',
            'message': get_custom_message('block-search-tool', default_msg)
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_search_tool(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))