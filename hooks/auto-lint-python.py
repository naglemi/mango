#!/usr/bin/env python3
import json
import sys
import subprocess
import tempfile
import os

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Only check Python files
if tool_name in ["Write", "Edit", "MultiEdit"]:
    file_path = tool_input.get("file_path", "")
    
    if not file_path.endswith('.py'):
        sys.exit(0)
    
    # Get the content that will be written
    content = ""
    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        # For Edit, we can't check the full file, just the new content
        content = tool_input.get("new_string", "")
        # Basic syntax check only
        if content:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_file = f.name
            
            result = subprocess.run(
                ['python3', '-m', 'py_compile', temp_file],
                capture_output=True,
                text=True
            )
            os.unlink(temp_file)
            
            if result.returncode != 0:
                print("PYTHON SYNTAX ERROR!", file=sys.stderr)
                print("", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
                sys.exit(2)
        sys.exit(0)
    elif tool_name == "MultiEdit":
        # Can't easily check MultiEdit
        sys.exit(0)
    
    # For Write operations, check the full content
    if content:
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        # Run Python's built-in compile check
        result = subprocess.run(
            ['python3', '-m', 'py_compile', temp_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("PYTHON SYNTAX ERROR DETECTED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("The Python code has syntax errors:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            
            # Also run ast check for better error messages
            ast_result = subprocess.run(
                ['python3', '-c', f'import ast; ast.parse(open("{temp_file}").read(), "{file_path}")'],
                capture_output=True,
                text=True
            )
            if ast_result.stderr:
                print("", file=sys.stderr)
                print("Detailed error:", file=sys.stderr)
                print(ast_result.stderr, file=sys.stderr)
            
            os.unlink(temp_file)
            sys.exit(2)
        
        # Check for basic indentation issues
        result = subprocess.run(
            ['python3', '-m', 'tabnanny', temp_file],
            capture_output=True,
            text=True
        )
        
        if result.stdout and 'inconsistent' in result.stdout.lower():
            print("INDENTATION ERROR DETECTED!", file=sys.stderr)
            print("", file=sys.stderr)
            print("The Python code has inconsistent indentation:", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            os.unlink(temp_file)
            sys.exit(2)
        
        os.unlink(temp_file)

sys.exit(0)