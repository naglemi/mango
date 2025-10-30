#!/usr/bin/env python3
"""
Hook to strictly limit line count in files - blocks ALL edits to files over limit.
Configurable via MAX_LINE_COUNT environment variable (default: 300).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_file_line_limit(event):
    """Block any edits to files that exceed line limit."""
    
    # Get line count limit from environment
    max_lines = int(os.environ.get('MAX_LINE_COUNT', '300'))
    
    # Only check Edit, MultiEdit, and Write operations
    if event.get('tool') not in ['Edit', 'MultiEdit', 'Write']:
        return None
    
    params = event.get('params', {})
    file_path = params.get('file_path')
    
    if not file_path:
        return None
    
    if event.get('tool') == 'Write':
        # Check content being written
        content = params.get('content', '')
        new_lines = len(content.splitlines())
        
        if new_lines > max_lines:
            return {
                'action': 'stop',
                'message': f"Cannot write file with {new_lines} lines (limit: {max_lines}). Break into smaller files."
            }
    
    else:  # Edit or MultiEdit
        # Check if file already exceeds limit
        try:
            if Path(file_path).exists():
                with open(file_path, 'r') as f:
                    current_lines = len(f.readlines())
                
                if current_lines > max_lines:
                    return {
                        'action': 'stop',
                        'message': f"Cannot edit file with {current_lines} lines (limit: {max_lines}). File is too large - refactor into smaller files first."
                    }
                
                # For edits, also check if result would exceed limit
                if event.get('tool') == 'Edit':
                    old_string = params.get('old_string', '')
                    new_string = params.get('new_string', '')
                    
                    old_lines = len(old_string.splitlines())
                    new_lines = len(new_string.splitlines())
                    new_total = current_lines - old_lines + new_lines
                    
                    if new_total > max_lines:
                        return {
                            'action': 'stop',
                            'message': f"Edit would result in {new_total} lines (limit: {max_lines}). Break into smaller files."
                        }
                
                elif event.get('tool') == 'MultiEdit':
                    edits = params.get('edits', [])
                    
                    net_change = 0
                    for edit in edits:
                        old_string = edit.get('old_string', '')
                        new_string = edit.get('new_string', '')
                        net_change += len(new_string.splitlines()) - len(old_string.splitlines())
                    
                    new_total = current_lines + net_change
                    
                    if new_total > max_lines:
                        return {
                            'action': 'stop',
                            'message': f"Edits would result in {new_total} lines (limit: {max_lines}). Break into smaller files."
                        }
        except:
            # If can't read file, allow the operation
            pass
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_file_line_limit(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))