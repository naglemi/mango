# save as mcp_gpt5_proxy.py  (pip install fastmcp==2.* openai==1.* uvicorn)
import os, asyncio, openai
from fastmcp import FastMCP

openai.api_key = os.environ["OPENAI_API_KEY"]

server = FastMCP(name="gpt5_proxy")

@server.tool()
async def gpt5_chat(messages: list[dict]) -> str:
    """Consult OpenAI GPT-5 when you are stuck or need strategic advice."""
    try:
        # GPT-5 uses the Responses API
        input_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        response = await openai.AsyncOpenAI().responses.create(
            model="gpt-5",
            input=input_text,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"}
        )
        return response.output_text
    except Exception as e:
        if "Unsupported model" in str(e) or "model_not_found" in str(e) or "invalid_request_error" in str(e):
            error_msg = (
                "GPT-5 model is not available. DO NOT fall back to gpt-5-mini or any other model. "
                "Instead, send the complete plea to human via mcp__report__send_report for review. "
                "The plea workflow should handle this by checking execution mode."
            )
            raise ValueError(error_msg)
        else:
            raise e

if __name__ == "__main__":
    # stdio transport is simplest for local dev, HTTP/SSE also work
    server.run()