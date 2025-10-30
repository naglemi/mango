#!/usr/bin/env python3
"""
Hook to limit line count in files - allows edits that don't increase line count.
Configurable via MAX_LINE_COUNT environment variable (default: 300).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_line_increase(event):
    """Check if edit would increase line count beyond limit."""
    
    # Get line count limit from environment
    max_lines = int(os.environ.get('MAX_LINE_COUNT', '300'))
    
    # Only check Edit, MultiEdit, and Write operations
    if event.get('tool') not in ['Edit', 'MultiEdit', 'Write']:
        return None
    
    params = event.get('params', {})
    
    if event.get('tool') == 'Write':
        file_path = params.get('file_path')
        content = params.get('content', '')
        
        if not file_path:
            return None
            
        # Check new content line count
        new_lines = len(content.splitlines())
        
        if new_lines > max_lines:
            return {
                'action': 'stop',
                'message': f"File would have {new_lines} lines, exceeding limit of {max_lines}. Break into smaller files."
            }
    
    elif event.get('tool') == 'Edit':
        file_path = params.get('file_path')
        old_string = params.get('old_string', '')
        new_string = params.get('new_string', '')
        
        if not file_path:
            return None
        
        # Count line changes
        old_lines = len(old_string.splitlines())
        new_lines = len(new_string.splitlines())
        
        # Only block if lines would increase
        if new_lines > old_lines:
            # Try to read current file to check total
            try:
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        current_total = len(f.readlines())
                    
                    # Calculate new total
                    new_total = current_total - old_lines + new_lines
                    
                    if new_total > max_lines:
                        return {
                            'action': 'stop',
                            'message': f"Edit would increase file to {new_total} lines, exceeding limit of {max_lines}"
                        }
            except:
                pass
    
    elif event.get('tool') == 'MultiEdit':
        file_path = params.get('file_path')
        edits = params.get('edits', [])
        
        if not file_path:
            return None
        
        # Calculate net line change
        net_change = 0
        for edit in edits:
            old_string = edit.get('old_string', '')
            new_string = edit.get('new_string', '')
            net_change += len(new_string.splitlines()) - len(old_string.splitlines())
        
        # Only block if net change increases lines
        if net_change > 0:
            try:
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        current_total = len(f.readlines())
                    
                    new_total = current_total + net_change
                    
                    if new_total > max_lines:
                        return {
                            'action': 'stop',
                            'message': f"Edits would increase file to {new_total} lines, exceeding limit of {max_lines}"
                        }
            except:
                pass
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_line_increase(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))