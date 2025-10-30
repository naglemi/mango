#!/usr/bin/env python3

"""
Grok-proxy MCP server using X.AI's Grok-4 model
Provides "phone a friend" functionality to consult X.AI's Grok-4 reasoning model
"""

import json
import sys
import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('/tmp/grok-proxy.log', mode='a')
    ]
)
logger = logging.getLogger('grok-proxy')

class CircuitBreaker:
    """Simple circuit breaker for API calls"""
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        elif self.state == "open":
            if datetime.now().timestamp() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
        logger.info("Circuit breaker reset - service healthy")

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")

# Global circuit breaker instance
circuit_breaker = CircuitBreaker()

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
            "name": "grok_proxy",
            "version": "1.0.0"
        }
    }

def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "grok_health",
                "description": "Check the health status of the Grok-4 MCP proxy and API connectivity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": false
                }
            },
            {
                "name": "grok_chat",
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
                        },
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional array of file paths to include in the analysis. Files will be read and included with proper delimiters."
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

async def check_api_health() -> Dict[str, Any]:
    """Check Grok-4 API health status"""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable is required")

    health_status = {
        "status": "unknown",
        "timestamp": datetime.now().isoformat(),
        "circuit_breaker": circuit_breaker.state,
        "api_connectivity": False,
        "response_time_ms": None,
        "error": None
    }

    if not circuit_breaker.can_execute():
        health_status["status"] = "circuit_open"
        health_status["error"] = "Circuit breaker is open due to repeated failures"
        return health_status

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    test_data = {
        "messages": [{"role": "user", "content": "Health check"}],
        "model": "grok-4",
        "stream": False,
        "max_tokens": 10
    }

    start_time = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                health_status["response_time_ms"] = round(response_time, 2)

                if response.status == 200:
                    health_status["status"] = "healthy"
                    health_status["api_connectivity"] = True
                    circuit_breaker.record_success()
                else:
                    health_status["status"] = "unhealthy"
                    health_status["error"] = f"API returned status {response.status}"
                    circuit_breaker.record_failure()

    except asyncio.TimeoutError:
        health_status["status"] = "unhealthy"
        health_status["error"] = "Health check timeout"
        circuit_breaker.record_failure()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        circuit_breaker.record_failure()

    logger.info(f"Health check result: {health_status['status']}")
    return health_status

async def call_grok_api(messages):
    """Call X.AI's Grok-4 API with the provided messages"""
    if not circuit_breaker.can_execute():
        error_msg = f"Circuit breaker is {circuit_breaker.state} - service temporarily unavailable"
        logger.warning(error_msg)
        return f"Service temporarily unavailable: {error_msg}"

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

    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            logger.info(f"Calling Grok-4 API (attempt {retry_count + 1}/{max_retries})")
            async with aiohttp.ClientSession() as session:
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
                            logger.info(f"Tokens used - Completion: {usage.get('completion_tokens', 0)}, Reasoning: {usage.get('reasoning_tokens', 0)}")

                        circuit_breaker.record_success()
                        return full_response
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")

                        if response.status >= 500:  # Server errors - retry
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                                continue

                        circuit_breaker.record_failure()
                        return f"Error calling Grok-4 API: {response.status} - {error_text}"

        except asyncio.TimeoutError:
            logger.error("Request timeout after 5 minutes")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(2 ** retry_count)
                continue
            circuit_breaker.record_failure()
            return "Error: Grok-4 API request timed out after multiple retries"

        except aiohttp.ClientError as e:
            logger.error(f"Client error: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(2 ** retry_count)
                continue
            circuit_breaker.record_failure()
            return f"Error calling Grok-4 API: {str(e)}"

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            circuit_breaker.record_failure()
            return f"Error parsing Grok-4 API response: Invalid JSON"

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            circuit_breaker.record_failure()
            return f"Error calling Grok-4 API: {str(e)}"

    circuit_breaker.record_failure()
    return f"Failed to call Grok-4 API after {max_retries} retries"

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    try:
        if name == "grok_health":
            # Run health check
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                health_result = loop.run_until_complete(check_api_health())
            finally:
                loop.close()

            # Format health result as readable text
            status_emoji = "" if health_result["status"] == "healthy" else ""
            health_text = f"{status_emoji} **Grok-4 MCP Health Status**\n\n"
            health_text += f"**Status**: {health_result['status']}\n"
            health_text += f"**Timestamp**: {health_result['timestamp']}\n"
            health_text += f"**Circuit Breaker**: {health_result['circuit_breaker']}\n"
            health_text += f"**API Connectivity**: {'' if health_result['api_connectivity'] else ''}\n"

            if health_result['response_time_ms']:
                health_text += f"**Response Time**: {health_result['response_time_ms']}ms\n"

            if health_result['error']:
                health_text += f"**Error**: {health_result['error']}\n"

            return {
                "content": [
                    {
                        "type": "text",
                        "text": health_text
                    }
                ]
            }

        elif name == "grok_chat":
            messages = arguments.get("messages", [])
            files = arguments.get("files", [])

            if not messages:
                raise ValueError("messages parameter is required")

            # Process files if provided
            processed_messages = messages.copy()
            if files:
                file_contents = []
                for file_path in files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_contents.append(f"===== {file_path} =====\n{content}")
                    except Exception as e:
                        file_contents.append(f"===== {file_path} =====\n[ERROR: Could not read file - {str(e)}]")

                # Add file contents to the last user message
                if processed_messages and processed_messages[-1]["role"] == "user":
                    processed_messages[-1]["content"] += "\n\n## INCLUDED FILES FOR ANALYSIS\n\n" + "\n\n".join(file_contents)
                else:
                    # If no user message, create one with just the files
                    processed_messages.append({
                        "role": "user",
                        "content": "## INCLUDED FILES FOR ANALYSIS\n\n" + "\n\n".join(file_contents)
                    })

            # Run the async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                content = loop.run_until_complete(call_grok_api(processed_messages))
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

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool call failed for {name}: {str(e)}")
        raise ValueError(f"{name} failed: {str(e)}")

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