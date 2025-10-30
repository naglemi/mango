#!/usr/bin/env python3

"""
Enhanced GPT-5 proxy with web search capability
Searches the web first, then passes results to GPT-5 for analysis
"""

import json
import sys
import os
import asyncio
from openai import AsyncOpenAI
import requests
from urllib.parse import quote

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
            "name": "gpt5_proxy_with_search",
            "version": "2.0.0"
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
            },
            {
                "name": "gpt5_search_and_analyze",
                "description": "Search the web for information and have GPT-5 analyze the results. Perfect for reading docs, finding current information, etc.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find information"
                        },
                        "task": {
                            "type": "string",
                            "description": "What GPT-5 should do with the search results (e.g., 'summarize the installation steps', 'extract the API endpoints')"
                        }
                    },
                    "required": ["query", "task"]
                }
            }
        ]
    }

def search_web(query):
    """Search the web using Brave Search API"""
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        # Fallback to DuckDuckGo HTML search if no Brave API key
        return search_duckduckgo(query)
    
    url = f"https://api.search.brave.com/res/v1/web/search?q={quote(query)}"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("web", {}).get("results", [])[:5]:  # Top 5 results
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", "")
            })
        return results
    except Exception as e:
        print(f"[gpt5-proxy] Brave search failed: {e}, falling back to DuckDuckGo", file=sys.stderr)
        return search_duckduckgo(query)

def search_duckduckgo(query):
    """Fallback search using DuckDuckGo instant answer API"""
    url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Get abstract if available
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Summary"),
                "url": data.get("AbstractURL", ""),
                "description": data.get("Abstract", "")
            })
        
        # Get related topics
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "Related",
                    "url": topic.get("FirstURL", ""),
                    "description": topic.get("Text", "")
                })
        
        if not results:
            results.append({
                "title": "Limited results",
                "url": "",
                "description": f"DuckDuckGo instant answers had limited results for '{query}'. Consider using Brave Search API for better results."
            })
        
        return results
    except Exception as e:
        print(f"[gpt5-proxy] DuckDuckGo search failed: {e}", file=sys.stderr)
        return [{
            "title": "Search failed",
            "url": "",
            "description": f"Could not search for '{query}'. Error: {str(e)}"
        }]

def estimate_prompt_tokens(messages):
    """Rough estimation of prompt tokens (4 chars ≈ 1 token)"""
    if isinstance(messages, str):
        return len(messages) // 4
    total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
    return total_chars // 4

def calc_max_tokens(messages):
    """Calculate safe max_completion_tokens based on prompt length"""
    env_limit = int(os.environ.get("GPT5_MAX_COMPLETION_TOKENS", "4096"))
    context_limit = 128000  # 128k tokens
    
    prompt_tokens = estimate_prompt_tokens(messages)
    available_room = max(context_limit - prompt_tokens - 100, 64)
    
    return min(env_limit, available_room)

async def call_gpt5(messages):
    """Call OpenAI GPT-5 model using the Responses API"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    client = AsyncOpenAI(api_key=api_key)
    max_tokens = calc_max_tokens(messages)
    
    for attempt in range(2):
        try:
            # Convert messages to input format
            if isinstance(messages, str):
                input_text = messages
            else:
                input_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            response = await client.responses.create(
                model="gpt-5",
                input=input_text,
                reasoning={"effort": "high"},
                text={"verbosity": "high"}
            )
            
            if hasattr(response, 'output_text'):
                return response.output_text
            else:
                return str(response)
            
        except Exception as e:
            if "Unsupported model" in str(e) or "model_not_found" in str(e):
                error_msg = "GPT-5 model is not available. Cannot proceed with analysis."
                print(f"[gpt5-proxy] ERROR: {error_msg}", file=sys.stderr)
                raise ValueError(error_msg)
            elif attempt == 0:
                continue
            raise ValueError(f"Failed to call GPT-5: {str(e)}")
    
    raise ValueError("GPT-5 call failed after retries")

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name == "gpt5_chat":
        messages = arguments.get("messages", [])
        if not messages:
            raise ValueError("messages parameter is required")
        
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
    
    elif name == "gpt5_search_and_analyze":
        query = arguments.get("query")
        task = arguments.get("task")
        
        if not query or not task:
            raise ValueError("Both 'query' and 'task' parameters are required")
        
        # Search the web
        print(f"[gpt5-proxy] Searching for: {query}", file=sys.stderr)
        search_results = search_web(query)
        
        # Format search results for GPT-5
        search_context = f"Web search results for '{query}':\n\n"
        for i, result in enumerate(search_results, 1):
            search_context += f"{i}. {result['title']}\n"
            search_context += f"   URL: {result['url']}\n"
            search_context += f"   {result['description']}\n\n"
        
        # Create prompt for GPT-5
        analysis_prompt = f"""Based on these web search results, {task}

{search_context}

Please provide a comprehensive analysis addressing the task."""
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                content = loop.run_until_complete(call_gpt5(analysis_prompt))
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
            raise ValueError(f"GPT-5 search and analysis failed: {str(e)}")
    
    else:
        raise ValueError(f"Unknown tool: {name}")

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
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                send_message(response)
                
            except Exception as e:
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