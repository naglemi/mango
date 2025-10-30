#!/usr/bin/env python3

"""
Simple ninjagrab MCP server using basic MCP protocol over stdio
Provides file collection functionality equivalent to ninjagrab.sh
"""

import json
import sys
import os
import subprocess
from pathlib import Path

def send_message(message):
    """Send a JSON-RPC message to stdout"""
    print(json.dumps(message))
    sys.stdout.flush()

def receive_message():
    """Receive a JSON-RPC message from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None

def handle_initialize(params):
    """Handle initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "ninjagrab",
            "version": "1.0.0"
        }
    }

def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "ninjagrab_collect",
                "description": "Concatenate multiple files with clear delimiters and save to ninjagrab-out.txt. Returns the output filepath instead of sending content directly. IMPORTANT: Only processes .json, .yaml, .yml, .py, .R, and .sh files. Other file types are filtered out.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to collect and concatenate (only .json, .yaml, .yml, .py, .R, .sh files)"
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Working directory to run from (defaults to current directory)",
                            "default": "."
                        }
                    },
                    "required": ["files"]
                }
            }
        ]
    }

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name != "ninjagrab_collect":
        raise ValueError(f"Unknown tool: {name}")
    
    files = arguments.get("files", [])
    working_directory = arguments.get("working_directory", ".")
    
    # Change to working directory
    original_cwd = os.getcwd()
    try:
        os.chdir(working_directory)
        
        # Try to use the actual ninjagrab.sh script if available
        ninjagrab_script = os.environ.get('NINJAGRAB_SCRIPT_PATH')
        if ninjagrab_script and os.path.isfile(ninjagrab_script):
            try:
                # Use the actual ninjagrab.sh script
                cmd = [ninjagrab_script] + files
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                output_file = "ninjagrab-out.txt"

                errors = []
                if result.returncode != 0:
                    errors.append(f"ninjagrab.sh exited with code {result.returncode}")
                    if result.stderr:
                        errors.append(result.stderr.strip())
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Files processed: {len([f for f in files if os.path.isfile(f)])}\n"
                                   f"Output saved to: {os.path.abspath(output_file)}\n"
                                   f"Errors: {errors}\n\n"
                                   f"Use the Read tool to view the collected content."
                        }
                    ]
                }
                
            except Exception as e:
                # Fall back to Python implementation if script fails
                pass
        
        # Python implementation fallback
        output_file = "ninjagrab-out.txt"
        errors = []
        files_processed = 0
        files_filtered = 0

        # Allowed extensions
        allowed_extensions = {'.json', '.yaml', '.yml', '.py', '.R', '.sh'}

        # Truncate/create output file
        with open(output_file, 'w') as out_f:
            pass

        for file_path in files:
            try:
                path = Path(file_path)

                # Check file extension
                file_extension = path.suffix
                if not file_extension or file_extension not in allowed_extensions:
                    filter_msg = f"[FILTERED] Skipping {file_path} (extension {file_extension if file_extension else 'none'} not allowed - only json, yaml, yml, py, R, sh allowed)"
                    with open(output_file, 'a') as out_f:
                        out_f.write(filter_msg + '\n')
                    files_filtered += 1
                    continue

                if not path.is_file():
                    error_msg = f"[ERROR] {file_path} not found or not a regular file"
                    errors.append(error_msg)
                    with open(output_file, 'a') as out_f:
                        out_f.write(error_msg + '\n')
                    continue

                # Create delimiter
                delimiter = f"===== {file_path} ====="

                # Read file contents and write to output file
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read()

                with open(output_file, 'a') as out_f:
                    out_f.write(delimiter + '\n')
                    out_f.write(file_content)
                    out_f.write('\n')

                files_processed += 1

            except Exception as e:
                error_msg = f"[ERROR] Failed to process {file_path}: {str(e)}"
                errors.append(error_msg)
                with open(output_file, 'a') as out_f:
                    out_f.write(error_msg + '\n')
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Files processed: {files_processed}\n"
                           f"Files filtered: {files_filtered}\n"
                           f"Output saved to: {os.path.abspath(output_file)}\n"
                           f"Errors: {errors}\n\n"
                           f"Use the Read tool to view the collected content."
                }
            ]
        }
        
    finally:
        os.chdir(original_cwd)

def main():
    """Main MCP server loop"""
    while True:
        try:
            request = receive_message()
            if request is None:
                break
            
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            try:
                if method == "initialize":
                    result = handle_initialize(params)
                elif method == "tools/list":
                    result = handle_tools_list()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = handle_tools_call(tool_name, arguments)
                else:
                    raise ValueError(f"Unknown method: {method}")
                
                # Send success response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                send_message(response)
                
            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                send_message(error_response)
                
        except KeyboardInterrupt:
            break
        except Exception:
            break

if __name__ == "__main__":
    main()