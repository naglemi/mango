#!/usr/bin/env python3
import json
import subprocess
import sys

def test_hook(command, should_block=False):
    """Test the protect-env-vars.py hook with a given command."""
    
    # Prepare the input data as it would come from Claude Code
    input_data = {
        "session_id": "test123",
        "transcript_path": "/tmp/test.jsonl",
        "cwd": "/home/ubuntu/mango",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": command
        }
    }
    
    # Run the hook script
    result = subprocess.run(
        ["/home/ubuntu/mango/hooks/protect-env-vars.py"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )
    
    # Check if the result matches expectations
    if should_block:
        if result.returncode == 2:
            print(f"PASS (blocked as expected): {command}")
            if result.stderr:
                print(f"  Message: {result.stderr.split(chr(10))[0]}")
            return True
        else:
            print(f" FAIL (should have blocked): {command}")
            return False
    else:
        if result.returncode == 0:
            print(f"PASS (allowed as expected): {command}")
            return True
        else:
            print(f" FAIL (should have allowed): {command}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            return False

def main():
    print("Testing protect-env-vars.py hook...")
    print("=" * 60)
    
    tests = [
        # Commands that SHOULD BE BLOCKED
        ("export HUMAN_INPUT='test'", True),
        ("HUMAN_VALUE=123", True),
        ("export MY_HUMAN_VAR='something'", True),
        ("timeout=5000", True),
        ("export timeout=30", True),
        ("unset HUMAN_CONFIG", True),
        ("unset timeout", True),
        ("declare HUMAN_MODE=active", True),
        ("eval 'HUMAN_FLAG=1'", True),
        ("echo 'HUMAN_VAR=test' > config.sh", True),
        ("echo 'timeout=100' >> settings.conf", True),
        
        # Commands that SHOULD BE ALLOWED
        ("echo 'This is a human-readable message'", False),
        ("ls -la", False),
        ("cd /tmp", False),
        ("export OTHER_VAR='value'", False),
        ("MY_VAR=123", False),
        ("echo 'Setting timeout for process'", False),
        ("grep HUMAN file.txt", False),
        ("cat timeout.conf", False),
        ("echo \$HUMAN_VAR", False),  # Reading, not modifying
        ("echo \$timeout", False),  # Reading, not modifying
    ]
    
    passed = 0
    failed = 0
    
    for command, should_block in tests:
        if test_hook(command, should_block):
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed!")
        sys.exit(0)
    else:
        print(" Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()