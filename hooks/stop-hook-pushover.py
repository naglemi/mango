#!/usr/bin/env python3
"""
Claude Stop hook - sends Pushover notification when Claude finishes responding
"""

import json
import sys
import os
import subprocess
from datetime import datetime

def get_last_assistant_response(transcript_path):
    """Extract the last assistant response from transcript"""
    if not os.path.exists(transcript_path):
        return None
    
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()
        
        # Look for the last assistant response with text content
        for line in reversed(lines):
            try:
                data = json.loads(line.strip())
                # Check if this is an assistant message
                if data.get("type") == "assistant" or (data.get("message", {}).get("role") == "assistant"):
                    # Try different content locations
                    message = data.get("message", {})
                    content_array = message.get("content", [])
                    
                    # Look for text content in the content array
                    for item in content_array:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            if text:
                                return str(text)
                    
                    # Fallback to old format
                    if isinstance(content_array, str) and content_array:
                        return str(content_array)
            except:
                continue
        return None
    except:
        return None

def clean_text(text, max_length=900):
    """Clean and truncate text for notification"""
    if not text:
        return "No response text"
    
    text = str(text).strip()
    
    # If it's JSON tool responses, try to extract meaningful parts
    if text.startswith('[') or text.startswith('{'):
        # Just take first 900 chars of JSON
        text = text[:max_length] + "..." if len(text) > max_length else text
    else:
        # For regular text, truncate nicely
        if len(text) > max_length:
            text = text[:max_length] + "..."
    
    return text

def send_pushover(message, title):
    """Send Pushover notification"""
    app_token = os.environ.get('PUSHOVER_APP_TOKEN')
    user_key = os.environ.get('PUSHOVER_USER_KEY')
    
    if not app_token or not user_key:
        return False
    
    cmd = [
        'curl', '-s',
        '-F', f'token={app_token}',
        '-F', f'user={user_key}',
        '-F', f'title={title}',
        '-F', f'message={message}',
        'https://api.pushover.net/1/messages.json'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return response.get('status') == 1
    except:
        pass
    
    return False

def main():
    """Main hook function"""
    # Always log that we started
    with open("/tmp/stop-hook-debug.log", "a") as f:
        f.write(f"\n{datetime.now()}: Hook started\n")
    
    try:
        # Read hook input
        input_data = json.load(sys.stdin)
        
        # Log the input
        with open("/tmp/stop-hook-debug.log", "a") as f:
            f.write(f"{datetime.now()}: Input: {json.dumps(input_data)}\n")
        
        # Check if this is a recursive stop hook call
        if input_data.get('stop_hook_active', False):
            # Don't trigger again to avoid infinite loop
            sys.exit(0)
        
        session_id = input_data.get('session_id', 'unknown')[:8]
        transcript_path = input_data.get('transcript_path')
        
        # Extract folder name from transcript path
        folder_name = "Claude"
        if transcript_path and "-home-ubuntu-" in transcript_path:
            # Extract from path like /home/ubuntu/.claude/projects/-home-ubuntu-mango/...
            parts = transcript_path.split("-home-ubuntu-")
            if len(parts) > 1:
                folder_name = parts[1].split("/")[0]
        
        if transcript_path:
            # Get the last response
            response = get_last_assistant_response(transcript_path)
            
            with open("/tmp/stop-hook-debug.log", "a") as f:
                f.write(f"{datetime.now()}: Transcript path: {transcript_path}\n")
                f.write(f"{datetime.now()}: Response found: {response is not None}\n")
            
            if response:
                # Get hostname
                hostname = "unknown"
                try:
                    import socket
                    hostname = socket.gethostname()
                except:
                    # Try subprocess if socket fails
                    try:
                        result = subprocess.run(['hostname'], capture_output=True, text=True)
                        if result.returncode == 0:
                            hostname = result.stdout.strip()
                    except:
                        pass
                
                # Clean and format message with hostname
                clean_response = clean_text(response)
                clean_response = f"{hostname}: {clean_response}"
                
                # Try to read the latest report URL
                report_url = None
                try:
                    url_file = os.path.join(os.getcwd(), 'temp', 'latest-report-url.txt')
                    if os.path.exists(url_file):
                        with open(url_file, 'r') as f:
                            report_url = f.read().strip()
                except:
                    pass  # No report URL, that's fine
                
                # Add report URL to message if available
                if report_url:
                    clean_response += f"\n\nLatest Report: {report_url}"
                
                title = f"{folder_name} [{session_id}]"
                
                with open("/tmp/stop-hook-debug.log", "a") as f:
                    f.write(f"{datetime.now()}: Sending pushover: {title}\n")
                    f.write(f"{datetime.now()}: Report URL included: {report_url is not None}\n")
                
                if send_pushover(clean_response, title):
                    # Success - return normal exit
                    with open("/tmp/stop-hook-debug.log", "a") as f:
                        f.write(f"{datetime.now()}: Pushover sent successfully\n")
                    sys.exit(0)
                else:
                    with open("/tmp/stop-hook-debug.log", "a") as f:
                        f.write(f"{datetime.now()}: Pushover failed\n")
        
        # If we get here, something didn't work but don't block
        sys.exit(0)
        
    except Exception as e:
        # Don't block Claude on errors - but log what happened
        with open("/tmp/stop-hook-debug.log", "a") as f:
            f.write(f"{datetime.now()}: EXCEPTION: {str(e)}\n")
            f.write(f"{datetime.now()}: Exception type: {type(e).__name__}\n")
            import traceback
            f.write(f"{datetime.now()}: Traceback:\n{traceback.format_exc()}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()