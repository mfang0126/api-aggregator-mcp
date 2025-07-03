"""Main application entry point for the API Aggregator MCP Server."""

import asyncio
import uvicorn
import structlog
from typing import Dict, Any

from .server import MCPServer
from .utils.config import get_settings, validate_api_keys
from .tools.weather import get_weather_handler, WEATHER_TOOL_SCHEMA
from .tools.news import get_news_handler, NEWS_TOOL_SCHEMA
from .tools.stock import (
    get_stock_price_handler, 
    search_stocks_handler,
    STOCK_PRICE_TOOL_SCHEMA, 
    STOCK_SEARCH_TOOL_SCHEMA
)


logger = structlog.get_logger(__name__)


def create_app() -> MCPServer:
    """Create and configure the MCP server application."""
    settings = get_settings()
    
    # Initialize the MCP server
    mcp_server = MCPServer(settings)
    
    # Validate API keys and register available tools
    available_apis = validate_api_keys()
    logger.info("API key validation", available_apis=available_apis)
    
    # Register weather tool if API key is available
    if available_apis["weather"]:
        mcp_server.register_tool(
            name="get_weather",
            description="Get current weather information for a specified city",
            input_schema=WEATHER_TOOL_SCHEMA,
            handler=get_weather_handler,
        )
        logger.info("Weather tool registered")
    else:
        logger.warning("Weather tool not registered - missing OpenWeatherMap API key")
    
    # Register news tool if API key is available
    if available_apis["news"]:
        mcp_server.register_tool(
            name="get_news",
            description="Get latest news headlines by topic, category, or country",
            input_schema=NEWS_TOOL_SCHEMA,
            handler=get_news_handler,
        )
        logger.info("News tool registered")
    else:
        logger.warning("News tool not registered - missing News API key")
    
    # Register stock tools if API key is available
    if available_apis["stock"]:
        mcp_server.register_tool(
            name="get_stock_price",
            description="Get current stock price and trading information for a given symbol",
            input_schema=STOCK_PRICE_TOOL_SCHEMA,
            handler=get_stock_price_handler,
        )
        mcp_server.register_tool(
            name="search_stocks",
            description="Search for stock symbols by company name or keywords",
            input_schema=STOCK_SEARCH_TOOL_SCHEMA,
            handler=search_stocks_handler,
        )
        logger.info("Stock tools registered")
    else:
        logger.warning("Stock tools not registered - missing Alpha Vantage API key")
    
    logger.info(
        "MCP Server initialized",
        tools_registered=len(mcp_server._tools),
        available_tools=list(mcp_server._tools.keys()),
        debug=settings.debug,
    )
    
    return mcp_server


def main() -> None:
    """Main entry point for running the server."""
    settings = get_settings()
    
    # Create the MCP server
    mcp_server = create_app()
    app = mcp_server.get_app()
    
    # Configure logging level
    import logging
    logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
    
    logger.info(
        "Starting API Aggregator MCP Server",
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
    )
    
    # Run the server
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )


if __name__ == "__main__":
    main() 