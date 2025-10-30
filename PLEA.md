# Technical Analysis Request - Claude State Detection for Multi-Agent PyAutoGUI Monitoring

## Problem Summary

**Current Issue**: Need a robust, efficient method to detect Claude Code's working/waiting state for PyAutoGUI-based monitoring of multiple parallel tmux panes running different Claude agents.

**Impact**:
- Cannot reliably automate tmux pane management without knowing agent state
- Existing approaches (file-based state tracking via hooks) are too complex and not robust for parallel agents
- Need a "positive indicator" that can be visually parsed from status bar, not relying on absence of signals
- Must work universally across multiple simultaneous Claude sessions without state collision

## Technical Analysis

### A. Root Cause Analysis

**Primary Challenge**: Claude Code's status line JSON does not include a state field indicating whether the agent is:
- Actively working (processing, executing tools)
- Waiting for user input
- Idle between operations

**Current Status Line JSON Structure** (per official docs):
```json
{
  "hook_event_name": "Status",
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "model": {
    "id": "string",
    "display_name": "string"
  },
  "workspace": {
    "current_dir": "string",
    "project_dir": "string"
  },
  "version": "string",
  "output_style": {
    "name": "string"
  },
  "cost": {
    "total_cost_usd": "number",
    "total_duration_ms": "number",
    "total_api_duration_ms": "number",
    "total_lines_added": "number",
    "total_lines_removed": "number"
  }
}
```

**Missing**: No `state`, `busy`, `waiting`, or similar field that directly indicates agent status.

**Contributing Factors**:
1. Status line updates every 300ms max, but only provides contextual session data
2. Hooks can detect events (Stop, UserPromptSubmit, PreToolUse, PostToolUse) but cannot directly update status line
3. Multiple parallel agents would overwrite shared state files
4. Transcript parsing would require reading large JSONL files repeatedly (inefficient)

### B. Complete Solution History

#### Attempt 1: Session-Specific State Files via Hooks
**What was tried**:
- Use Stop hook to write "WAITING" to `~/.claude-state-{session_id}`
- Use UserPromptSubmit hook to write "WORKING" to same file
- Status line script reads from session-specific file
- Display state in status bar for PyAutoGUI to parse

**Why we thought it would work**:
- Session ID makes files unique per agent
- Hooks fire at right times (Stop = waiting, UserPromptSubmit = working)
- Status line can read files and display content

**What happened**:
User rejected this approach before implementation

**Why it failed**:
- "Overly complex and not robust enough"
- Relies on external file state management
- Requires hook + status line script coordination
- Not checking state "programmatically" but via "hacky" file reading

**Side effects**: None (not implemented)

#### Attempt 2: Transcript-Based State Detection
**What was considered**:
- Status line script reads last few lines of transcript.jsonl
- Parse JSON to detect if last entry is:
  - Assistant message with text = Claude just finished (WAITING)
  - Assistant message with tool_use = Claude is working
  - User message = Claude should be working

**Why we thought it would work**:
- Transcript path is available in status line JSON
- Contains complete conversation state
- No external state files needed

**What happened**:
Not yet attempted - exploring efficiency concerns

**Current concerns**:
- Transcript files can be large (100KB+ observed in projects directory)
- Parsing JSON on every 300ms status update could be expensive
- Would need to tail file and parse JSONL efficiently
- Unclear if transcript updates synchronously with actual state changes

#### Attempt 3: Process State Inspection
**What was considered**:
- Check if Claude process is waiting on stdin vs actively processing
- Use ps/proc to inspect process state

**Why it might work**:
- Direct process-level state inspection
- No file management needed

**Current concerns**:
- No clear way to identify which process corresponds to which tmux pane/session
- Process state might not map cleanly to "working vs waiting for user"
- May require root/elevated permissions for full proc inspection

#### Attempt 4: Cost Field Delta Detection
**What was considered**:
- Track changes in cost.total_api_duration_ms between status updates
- If incrementing = working (API calls active)
- If static = waiting

**Why it might work**:
- No external state needed
- Available in status line JSON

**Current concerns**:
- Only detects API activity, not local tool execution (Bash, Read, etc.)
- May have delays between tool completion and waiting state
- Requires stateful tracking across status line invocations

### C. Current System State

**Environment Configuration**:
- Claude Code version: Unknown (not in status bar JSON)
- Project directory: /home/ubuntu/mango
- Working with hooks infrastructure already in place
- Stop hook currently configured: `/home/ubuntu/mango/hooks/stop-hook-pushover.py`
- Hook parses transcript.jsonl successfully for Pushover notifications

**Existing Hook Infrastructure**:
```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "python3 /home/ubuntu/mango/hooks/stop-hook-pushover.py",
        "timeout": 5
      }
    ]
  }
}
```

**Transcript File Format** (observed):
- Location: `~/.claude/projects/{project_encoded}/{session_id}.jsonl`
- Format: JSONL (one JSON object per line)
- Entry types observed: `{"type": "assistant", "message": {"role": "assistant", "content": [...]}}`
- Content types: `"text"`, `"tool_use"`, `"tool_result"`

**Session Management**:
- Session IDs stored in: `~/.claude/session-env/{session_id}/`
- Multiple active sessions observed (29 session directories)
- Most recent: `5825426f-b040-4e5a-9b30-5f6654293f59`

**Filesystem Layout**:
```
~/.claude/
├── settings.json          # Hook configuration
├── session-env/           # Session-specific directories
│   └── {session_id}/      # Per-session data
├── projects/              # Transcript storage
│   └── {project_encoded}/
│       └── {session_id}.jsonl  # Conversation transcript
└── history.jsonl          # Global history (33MB)
```

## Specific Help Needed

### 1. Missing Documentation Fields
**Question**: Are there undocumented fields in the status line JSON that indicate agent state?
- The official docs show specific fields, but implementations may include additional fields
- Fields like `is_busy`, `waiting_for_input`, `last_event`, or similar would solve this immediately
- Can you confirm if such fields exist but are undocumented?

### 2. Efficient Transcript Parsing Strategy
**Question**: What's the most efficient way for a status line script to detect state from transcript.jsonl?
- Given transcripts can be 100KB-1MB+, full parsing every 300ms is expensive
- Options considered:
  - Tail last N lines and parse backwards until finding assistant message
  - Use file seeking to read from end backwards
  - Track file size/mtime and only re-parse on changes
  - Use inotify/fswatch for change detection
- Which approach would you recommend for minimal overhead?
- Is transcript guaranteed to be flushed/updated before status line is invoked?

### 3. Alternative State Signals
**Question**: What other signals are available that could indicate Claude's state?
- Process state inspection (specific attributes to check?)
- IPC mechanisms (sockets, pipes, shared memory?)
- Environment variables set differently during working vs waiting?
- Lock files or semaphores?
- Any Claude Code internals that expose state without requiring transcript parsing?

### 4. Hook Timing Guarantees
**Question**: Can hooks provide reliable state tracking with proper timing?
- If Stop hook writes state and immediately exits, is status line guaranteed to see that state?
- Can we rely on hook execution order: `PreToolUse` → [Claude working] → `PostToolUse` → [more work] → `Stop` → [waiting]?
- Is there a hook that fires on "resuming work after being idle"? (UserPromptSubmit happens before processing starts)

### 5. Status Line Script Capabilities
**Question**: Can status line scripts maintain state between invocations?
- Can we use environment variables that persist across status line calls?
- Can we write to a session-specific location that status line can access reliably?
- Is there a caching mechanism we can leverage?

## Specific Technical Questions

1. **Transcript Parsing Implementation**: If we must parse transcripts, what's the optimal implementation pattern for a bash/python status line script that minimizes overhead while ensuring accuracy?

2. **Multi-Agent Collision Avoidance**: For the file-based approach (if unavoidable), what's the most robust way to prevent race conditions and state collision across multiple parallel Claude agents?

## Current Context

**Project**: usability (tmux/PyAutoGUI automation tools)
**Branch**: 001-i-want-the
**Directory**: /home/ubuntu/mango
**Git Status**:
```
M hooks/configure-hooks.py
M hooks/hooks-installed.json
M hooks/stop-hook-pushover.py
```

**Recent Commits**:
```
f605eb8 feat: add Settings option to Mango launcher menu
94e6b5e feat: rename project to Mango and add mango-launcher alias
6978371 fix: remove blank padding from mobile menu popup edges
```

**Use Case**: Building PyAutoGUI automation to monitor tmux panes running multiple Claude agents, detect when each is waiting for input, and manage pane switching/commands accordingly.

## Quality Check

- [x] Error messages - N/A (no errors, this is a research/design question)
- [x] Solution history - Documented all approaches considered
- [x] System information - Provided Claude configuration, hooks, transcript format
- [x] Specific technical questions - 5 detailed questions with context
- [x] Code files - Included existing hook implementation showing transcript parsing
- [x] Complete file contents - stop-hook-pushover.py shows working transcript parser
- [x] Architecture context - Explained multi-agent parallel execution requirement

---

# Code and Configuration Files

## Current Hook Implementation (Stop Hook with Transcript Parsing)

===== /home/ubuntu/.claude/settings.json =====
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-file-versions.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-bad-filenames.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-filename-proliferation.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-homedir-edits.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Bash|Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-hook-editing.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/python-lint-before-run.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-error-hiding.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-sed-editing.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/protect-env-vars.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-git-stash.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-python-c-inline.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "python3 /home/ubuntu/mango/hooks/block-rm.py",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 /home/ubuntu/mango/hooks/stop-hook-pushover.py",
        "timeout": 5
      }
    ]
  },
  "alwaysThinkingEnabled": false
}
```

===== /home/ubuntu/mango/hooks/stop-hook-pushover.py =====
```python
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
            # Extract from path like /home/ubuntu/.claude/projects/-home-ubuntu-usability/...
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
```

## Transcript Format Example

Based on inspection of `~/.claude/projects/-home-ubuntu-usability/5825426f-b040-4e5a-9b30-5f6654293f59.jsonl`:

```json
{"type":"assistant","role":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"...","name":"Bash","input":{...}}]}}
```

Content types observed:
- `"text"` - Regular assistant text responses
- `"tool_use"` - Tool invocations (Bash, Read, Write, etc.)
- `"tool_result"` - Results from tool execution

State detection logic from existing hook:
- Last assistant message with `"type": "text"` in content = just finished responding (WAITING)
- Last assistant message with `"type": "tool_use"` in content = may still be working
- Need to determine if more sophisticated logic is required
