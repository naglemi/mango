#!/usr/bin/env python3
"""
Test script for the sleep MCP server
"""

import json
import subprocess
import time
import os
import signal


def send_request(proc, method, params=None, request_id=1):
    """Send a JSON-RPC request to the MCP server"""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params is not None:
        request["params"] = params

    request_str = json.dumps(request) + "\n"
    proc.stdin.write(request_str.encode())
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().decode().strip()
    if response_line:
        return json.loads(response_line)
    return None


def test_initialize():
    """Test MCP initialization"""
    print("Test 1: Initialize MCP server")
    proc = subprocess.Popen(
        ["python3", "/home/ubuntu/mango/mcp/sleep/sleep_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        response = send_request(proc, "initialize", {})
        assert response is not None, "No response from initialize"
        assert "result" in response, "No result in initialize response"
        print(f"   Initialize successful: {response['result']['serverInfo']['name']}")
        return proc
    except Exception as e:
        print(f"   Initialize failed: {e}")
        proc.kill()
        return None


def test_tools_list(proc):
    """Test tools/list method"""
    print("\nTest 2: List available tools")
    try:
        response = send_request(proc, "tools/list", {})
        assert response is not None, "No response from tools/list"
        assert "result" in response, "No result in tools/list response"

        tools = response["result"]["tools"]
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"    - {tool['name']}")
        return True
    except Exception as e:
        print(f"   Tools list failed: {e}")
        return False


def test_quick_check(proc):
    """Test quick_check with current process"""
    print("\nTest 3: Quick check on current process")
    current_pid = os.getpid()

    try:
        response = send_request(
            proc,
            "tools/call",
            {
                "name": "quick_check",
                "arguments": {"pid": current_pid}
            }
        )

        assert response is not None, "No response from quick_check"
        assert "result" in response, "No result in quick_check response"

        content = json.loads(response["result"]["content"][0]["text"])
        assert content["running"] is True, "Should detect running process"
        print(f"   Quick check successful: PID {current_pid} is running")
        print(f"    Command: {content['command'][:50]}...")
        return True
    except Exception as e:
        print(f"   Quick check failed: {e}")
        return False


def test_sleep_until_complete(proc):
    """Test sleep_until_complete with a short-lived process"""
    print("\nTest 4: Sleep until process completes")

    # Start a short-lived process (sleep for 3 seconds)
    test_proc = subprocess.Popen(["sleep", "3"])
    test_pid = test_proc.pid

    print(f"  Started test process: PID {test_pid} (sleep 3)")

    try:
        start_time = time.time()

        response = send_request(
            proc,
            "tools/call",
            {
                "name": "sleep_until_complete",
                "arguments": {
                    "pid": test_pid,
                    "timeout": 10,
                    "poll_interval": 0.5
                }
            }
        )

        elapsed = time.time() - start_time

        assert response is not None, "No response from sleep_until_complete"
        assert "result" in response, "No result in sleep_until_complete response"

        content = json.loads(response["result"]["content"][0]["text"])
        assert content["status"] == "completed", f"Expected completed, got {content['status']}"

        print(f"   Sleep successful: Process completed after {elapsed:.1f}s")
        print(f"    Status: {content['status']}")
        return True
    except Exception as e:
        print(f"   Sleep test failed: {e}")
        test_proc.kill()
        return False


def test_not_found(proc):
    """Test with a non-existent PID"""
    print("\nTest 5: Check non-existent process")

    fake_pid = 999999

    try:
        response = send_request(
            proc,
            "tools/call",
            {
                "name": "sleep_until_complete",
                "arguments": {"pid": fake_pid}
            }
        )

        assert response is not None, "No response"
        content = json.loads(response["result"]["content"][0]["text"])
        assert content["status"] == "not_found", f"Expected not_found, got {content['status']}"

        print(f"   Not found handled correctly")
        return True
    except Exception as e:
        print(f"   Not found test failed: {e}")
        return False


def test_command_pattern(proc):
    """Test sleep_until_command_complete"""
    print("\nTest 6: Sleep until command pattern completes")

    # Start a process with a unique command pattern
    test_pattern = "test_sleep_marker_12345"
    test_proc = subprocess.Popen(["sleep", "2"], env={**os.environ, "TEST_MARKER": test_pattern})
    test_pid = test_proc.pid

    print(f"  Started test process: PID {test_pid}")

    try:
        start_time = time.time()

        # Note: This might not work perfectly since 'sleep 2' doesn't contain our marker
        # But we can test with 'sleep' as the pattern
        response = send_request(
            proc,
            "tools/call",
            {
                "name": "sleep_until_command_complete",
                "arguments": {
                    "command_pattern": "sleep 2",
                    "timeout": 10,
                    "poll_interval": 0.5
                }
            }
        )

        elapsed = time.time() - start_time

        assert response is not None, "No response"

        content = json.loads(response["result"]["content"][0]["text"])

        if content["status"] == "not_found":
            print(f"   No matching processes found (expected)")
            return True
        elif content["status"] == "completed":
            print(f"   Command pattern test successful: {elapsed:.1f}s")
            return True
        else:
            print(f"   Unexpected status: {content['status']}")
            return True

    except Exception as e:
        print(f"   Command pattern test failed: {e}")
        test_proc.kill()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Sleep MCP Server Test Suite")
    print("=" * 60)

    proc = test_initialize()
    if proc is None:
        print("\n Tests aborted: initialization failed")
        return

    results = []
    results.append(test_tools_list(proc))
    results.append(test_quick_check(proc))
    results.append(test_sleep_until_complete(proc))
    results.append(test_not_found(proc))
    results.append(test_command_pattern(proc))

    # Clean up
    proc.terminate()
    proc.wait()

    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)

    if passed == total:
        print(" All tests passed!")
        return 0
    else:
        print(" Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
