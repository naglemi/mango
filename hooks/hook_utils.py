#!/usr/bin/env python3
"""
Utilities for Claude Code hooks
"""

import json
from pathlib import Path

def get_custom_message(hook_id: str, default_message: str = None) -> str:
    """Get custom message for a hook, or return default."""
    messages_file = Path(__file__).parent / "hook_messages.json"
    
    if messages_file.exists():
        try:
            with open(messages_file, 'r') as f:
                messages = json.load(f)
                return messages.get(hook_id, default_message)
        except:
            pass
    
    return default_message or "Hook triggered - action blocked."