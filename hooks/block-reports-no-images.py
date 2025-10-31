#!/usr/bin/env python3
"""
Hook to block MCP report sending without image attachments.
Ensures all reports include at least one image file.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_report_has_images(event):
    """Block reports that don't have image attachments."""
    
    # Only check mcp__report__send_report tool
    if event.get('tool') != 'mcp__report__send_report':
        return None
    
    params = event.get('params', {})
    files = params.get('files', [])
    
    # Check if any files are provided
    if not files:
        return {
            'action': 'stop',
            'message': 'Reports must include at least one image attachment. Add image files to the report.'
        }
    
    # Check if at least one file is an image
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.tif'}
    has_image = False
    
    for file_path in files:
        path = Path(file_path)
        if path.suffix.lower() in image_extensions:
            has_image = True
            break
    
    if not has_image:
        return {
            'action': 'stop',
            'message': 'Reports must include at least one image file (.png, .jpg, .jpeg, .gif, .bmp, .svg, .webp, .tiff). Current files do not contain any images.'
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_report_has_images(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))