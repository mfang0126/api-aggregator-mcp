#!/bin/bash

# API Aggregator MCP Server Startup Script
# This script runs the server in MCP stdio mode for integration with MCP clients

trap "echo -e '\n🛑 Server stopped by user (Ctrl+C)'; exit 0" SIGINT

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set MCP mode
export MCP_SERVER_MODE=mcp

# Set MCP server port
export MCP_SERVER_PORT=8000

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading additional variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "No .env file found, using environment variables from shell..."
fi

# Check if any API keys are provided
has_api_keys=false

if [ -n "$OPENWEATHER_API_KEY" ] && [ "$OPENWEATHER_API_KEY" != '${OPENWEATHER_API_KEY}' ]; then
    echo "✅ OpenWeatherMap API key found"
    has_api_keys=true
else
    echo "❌ OpenWeatherMap API key missing or invalid"
fi

if [ -n "$NEWS_API_KEY" ] && [ "$NEWS_API_KEY" != '${NEWS_API_KEY}' ]; then
    echo "✅ News API key found"
    has_api_keys=true
else
    echo "❌ News API key missing or invalid"
fi

if [ -n "$ALPHA_VANTAGE_API_KEY" ] && [ "$ALPHA_VANTAGE_API_KEY" != '${ALPHA_VANTAGE_API_KEY}' ]; then
    echo "✅ Alpha Vantage API key found"
    has_api_keys=true
else
    echo "❌ Alpha Vantage API key missing or invalid"
fi

# Exit if no valid API keys are found
if [ "$has_api_keys" = false ]; then
    echo ""
    echo "❌ ERROR: No valid API keys found!"
    echo ""
    echo "The MCP server requires at least one valid API key to register tools."
    echo "Please set environment variables in your shell (zshrc) or .env file:"
    echo ""
    echo "Option 1 - Add to ~/.zshrc:"
    echo "  export OPENWEATHER_API_KEY=your_api_key"
    echo "  export NEWS_API_KEY=your_api_key"
    echo "  export ALPHA_VANTAGE_API_KEY=your_api_key"
    echo ""
    echo "Option 2 - Create .env file with:"
    echo "  OPENWEATHER_API_KEY=your_api_key"
    echo "  NEWS_API_KEY=your_api_key"
    echo "  ALPHA_VANTAGE_API_KEY=your_api_key"
    echo ""
    echo "Get API keys from:"
    echo "  • OpenWeatherMap: https://openweathermap.org/api"
    echo "  • News API: https://newsapi.org/"
    echo "  • Alpha Vantage: https://www.alphavantage.co/support/#api-key"
    echo ""
    exit 1
fi

echo ""
echo "🚀 Starting API Aggregator Server..."
echo ""
echo "Choose mode:"
echo "1. MCP Server (for AI clients like Cursor IDE)"
echo "2. REST API Server (for web/HTTP clients)"
echo ""

# Check if mode is specified via environment variable
if [ "${SERVER_MODE}" = "api" ]; then
    echo "🌐 Starting as REST API server (SERVER_MODE=api)..."
    python -m src.main --api --port ${MCP_SERVER_PORT:-8000}
else
    echo "🤖 Starting as MCP server (default mode)..."
    echo "💡 Tip: Set SERVER_MODE=api to run as REST API instead"
    python -m src.main --mcp
fi 