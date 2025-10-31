"""
FastMCP server for fact-based time estimation from filesystem timestamps.
"""

import logging
import argparse
from mcp.server.fastmcp import FastMCP

from .tools.estimate_tool import EstimateTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Estimate MCP server.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Estimate MCP Server - Fact-based time estimation")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run as an SSE server instead of stdio"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for SSE server (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for SSE server (default: 8001)"
    )
    args = parser.parse_args()

    # Create the MCP server
    logger.info("Starting Estimate MCP server")
    mcp = FastMCP("estimate")

    # Register the estimation tool
    logger.info("Registering estimate tool")
    mcp.register_tool("analyze_completion", EstimateTool())

    # Run the server
    if args.serve:
        logger.info(f"Running as SSE server on {args.host}:{args.port}")
        mcp.run_sse(host=args.host, port=args.port)
    else:
        logger.info("Running as stdio server")
        mcp.run()

if __name__ == "__main__":
    main()
