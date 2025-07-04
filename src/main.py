"""Main entry point for FastMCP-based API Aggregator Server."""

import argparse
import asyncio
import structlog
import sys
from .fastmcp_server import get_fastmcp_server

logger = structlog.get_logger(__name__)


def main():
    """Main entry point for the dual-mode API Aggregator server."""
    parser = argparse.ArgumentParser(
        description="API Aggregator Server - Serve as MCP Server OR REST API",
        epilog="""
Examples:
  python -m src.main --mcp          # MCP mode for Cursor IDE, Claude, etc.
  python -m src.main --api          # REST API mode for HTTP clients
  python -m src.main --stdio        # MCP mode via stdio (alias for --mcp)
  python -m src.main --http         # REST API mode via HTTP (alias for --api)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--mcp", "--stdio", action="store_true", 
                           help="Run as MCP server (stdio transport) - for AI clients")
    mode_group.add_argument("--api", "--http", action="store_true",
                           help="Run as REST API server (HTTP transport) - for web clients")
    
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP mode (default: 127.0.0.1)")
    
    args = parser.parse_args()
    
    # Get the FastMCP server
    mcp = get_fastmcp_server()
    
    if args.api:
        # Run as REST API server
        logger.info("🌐 Starting as REST API server", host=args.host, port=args.port)
        print(f"🌐 REST API server starting at http://{args.host}:{args.port}", file=sys.stderr)
        print(f"📚 API docs available at http://{args.host}:{args.port}/docs", file=sys.stderr)
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        # Default to MCP mode (stdio) - no print statements to stdout
        logger.info("🤖 Starting as MCP server (stdio mode)")
        # Don't print anything to stdout in MCP mode - only JSON-RPC messages should go there
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main() 