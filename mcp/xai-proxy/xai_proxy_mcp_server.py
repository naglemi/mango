#!/usr/bin/env python3

"""
XAI-proxy MCP server using X.AI's Grok-4 model
Fresh implementation to test name-based conflict theory
"""

import json
import sys
import os
import asyncio
import aiohttp

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
            "name": "xai_proxy",
            "version": "1.0.0"
        }
    }

def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "xai_consult",
                "description": "Consult X.AI's Grok-4 reasoning model when you need deep thinking and complex problem solving.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {
                                        "type": "string",
                                        "enum": ["system", "user", "assistant"]
                                    },
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

async def call_xai_api(messages):
    """Call X.AI's Grok-4 API with the provided messages"""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable is required")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "messages": messages,
        "model": "grok-4",
        "stream": False,
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        try:
            print(f"[xai-proxy] Calling X.AI Grok-4 API...", file=sys.stderr)
            async with session.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    content = result["choices"][0]["message"]["content"]
                    reasoning = result["choices"][0]["message"].get("reasoning_content", "")

                    if reasoning:
                        full_response = f"## Reasoning Process\n{reasoning}\n\n## Response\n{content}"
                    else:
                        full_response = content

                    if "usage" in result:
                        usage = result["usage"]
                        print(f"[xai-proxy] Tokens used - Completion: {usage.get('completion_tokens', 0)}, Reasoning: {usage.get('reasoning_tokens', 0)}", file=sys.stderr)

                    return full_response
                else:
                    error_text = await response.text()
                    print(f"[xai-proxy] API error {response.status}: {error_text}", file=sys.stderr)
                    return f"Error calling X.AI API: {response.status} - {error_text}"

        except asyncio.TimeoutError:
            print("[xai-proxy] Request timeout after 5 minutes", file=sys.stderr)
            return "Error: X.AI API request timed out after 5 minutes"
        except Exception as e:
            print(f"[xai-proxy] Unexpected error: {str(e)}", file=sys.stderr)
            return f"Error calling X.AI API: {str(e)}"

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name != "xai_consult":
        raise ValueError(f"Unknown tool: {name}")

    messages = arguments.get("messages", [])
    if not messages:
        raise ValueError("messages parameter is required")

    # Run the async function in sync context
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            content = loop.run_until_complete(call_xai_api(messages))
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
        raise ValueError(f"XAI consultation failed: {str(e)}")

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