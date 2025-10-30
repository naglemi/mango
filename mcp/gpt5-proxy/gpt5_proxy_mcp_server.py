#!/usr/bin/env python3

"""
Simple gpt5-proxy MCP server using basic MCP protocol over stdio
Provides "phone a friend" functionality to consult OpenAI's GPT-5 model
"""

import json
import sys
import os
import asyncio
from openai import AsyncOpenAI

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
            "name": "gpt5_proxy",
            "version": "1.1.0"
        }
    }

def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "gpt5_chat",
                "description": "Consult OpenAI GPT-5 when you are stuck or need strategic advice.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            },
                            "description": "Array of chat messages in OpenAI format"
                        }
                    },
                    "required": ["messages"]
                }
            }
        ]
    }

def estimate_prompt_tokens(messages):
    """Rough estimation of prompt tokens (4 chars ≈ 1 token)"""
    total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
    return total_chars // 4

def calc_max_tokens(messages):
    """Calculate safe max_completion_tokens based on prompt length"""
    # Get configurable limit from environment
    env_limit = int(os.environ.get("GPT5_MAX_COMPLETION_TOKENS", "4096"))
    
    # GPT-5 has large context window (conservative estimate)
    context_limit = 128000  # 128k tokens
    
    # Estimate prompt tokens and calculate remaining room
    prompt_tokens = estimate_prompt_tokens(messages)
    available_room = max(context_limit - prompt_tokens - 100, 64)  # 100 token safety buffer
    
    # Use the smaller of env limit or available room
    return min(env_limit, available_room)

async def call_gpt5(messages):
    """Call OpenAI GPT-5 model using the Responses API"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    client = AsyncOpenAI(api_key=api_key)
    
    max_tokens = calc_max_tokens(messages)
    
    # Try up to 2 attempts (original + 1 retry)
    for attempt in range(2):
        try:
            # Try GPT-5 only - no fallback to mini version
            try:
                # GPT-5 uses the Responses API, not Chat Completions
                # Convert messages to input format
                input_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                
                response = await client.responses.create(
                    model="gpt-5",
                    input=input_text,
                    reasoning={"effort": "high"},
                    text={"verbosity": "high"}
                )
            except Exception as e:
                if "Unsupported model" in str(e) or "model_not_found" in str(e) or "invalid_request_error" in str(e):
                    error_msg = (
                        "GPT-5 model is not available. DO NOT fall back to gpt-5-mini or any other model. "
                        "Instead, send the complete plea to human via mcp__report__send_report for review. "
                        "The plea workflow should handle this by checking execution mode."
                    )
                    print(f"[gpt5-proxy] ERROR: {error_msg}", file=sys.stderr)
                    raise ValueError(error_msg)
                else:
                    raise e
            
            # Responses API returns output_text directly
            if hasattr(response, 'output_text'):
                return response.output_text
            else:
                return str(response)  # Fallback
            
            # Response was truncated - try to increase token limit for retry
            if attempt == 0:  # Only retry once
                # Double the token limit for retry, but respect context window
                context_limit = 128000
                prompt_tokens = estimate_prompt_tokens(messages)
                max_possible = max(context_limit - prompt_tokens - 100, 64)
                
                if max_possible > max_tokens:
                    max_tokens = min(max_possible, max_tokens * 2)
                    print(f"[gpt5-proxy] Response truncated, retrying with {max_tokens} tokens", file=sys.stderr)
                    continue
            
            # Could not increase tokens further, return truncated response with warning
            print(f"[gpt5-proxy] WARNING: Response may be truncated at {max_tokens} tokens", file=sys.stderr)
            if hasattr(response, 'output_text'):
                return response.output_text
            return str(response)
            
        except Exception as e:
            if attempt == 0:
                # Retry once on any error
                continue
            raise ValueError(f"Failed to call GPT-5: {str(e)}")
    
    # Should not reach here, but just in case
    raise ValueError("GPT-5 call failed after retries")

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name != "gpt5_chat":
        raise ValueError(f"Unknown tool: {name}")
    
    messages = arguments.get("messages", [])
    if not messages:
        raise ValueError("messages parameter is required")
    
    # Run the async function in sync context
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            content = loop.run_until_complete(call_gpt5(messages))
        finally:
            loop.close()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        }
        
    except Exception as e:
        raise ValueError(f"GPT-5 consultation failed: {str(e)}")

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