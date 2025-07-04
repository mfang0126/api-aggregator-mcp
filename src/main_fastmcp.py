"""Main entry point for FastMCP-based API Aggregator Server."""

import argparse
import structlog
from .fastmcp_server import get_fastmcp_server

logger = structlog.get_logger(__name__)


def main():
    """Main entry point for the FastMCP server."""
    parser = argparse.ArgumentParser(description="API Aggregator MCP Server (FastMCP)")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode for MCP clients")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP mode (default: 127.0.0.1)")
    
    args = parser.parse_args()
    
    # Get the FastMCP server
    mcp = get_fastmcp_server()
    
    if args.stdio:
        # Run in stdio mode (default for MCP clients)
        logger.info("Starting FastMCP server in stdio mode")
        mcp.run(transport="stdio")
    elif args.http:
        # Run in HTTP mode
        logger.info("Starting FastMCP server in HTTP mode", host=args.host, port=args.port)
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        # Default to stdio mode
        logger.info("Starting FastMCP server in stdio mode (default)")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main() 