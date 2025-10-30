#!/usr/bin/env python3
"""
Hook to block commits directly to main branch.
Forces use of feature branches and proper PR workflow.
"""

import json
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import get_custom_message

def check_commit_to_main(event):
    """Block git commits to main branch."""
    
    # Only check Bash commands
    if event.get('tool') != 'Bash':
        return None
    
    params = event.get('params', {})
    command = params.get('command', '')
    
    if not command:
        return None
    
    # Check for git commit commands
    if 'git commit' in command or 'git ci' in command:
        # Check current branch by looking for previous commands or branch indicators
        # This is a simple check - could be made more sophisticated
        import subprocess
        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=False)
            current_branch = result.stdout.strip()
            
            if current_branch in ['main', 'master']:
                default_msg = "Cannot commit directly to main branch! Create a feature branch first: git checkout -b feature-name"
                return {
                    'action': 'stop',
                    'message': get_custom_message('block-commit-to-main', default_msg)
                }
        except:
            # If we can't determine branch, allow the commit
            pass
    
    # Also block git push to main
    if re.search(r'git\s+push.*\s+(origin\s+)?(main|master)', command):
        default_msg = "Cannot push directly to main branch! Use feature branches and pull requests."
        return {
            'action': 'stop',
            'message': get_custom_message('block-commit-to-main', default_msg)
        }
    
    return None

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    result = check_commit_to_main(event)
    
    if result:
        print(json.dumps(result))
        sys.exit(0)
    
    print(json.dumps({}))