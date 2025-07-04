#!/bin/bash

# API Aggregator - MCP Server Mode
# Runs the server for MCP clients (Cursor IDE, Claude, etc.)

trap "echo -e '\n🛑 Server stopped by user (Ctrl+C)' >&2; exit 0" SIGINT

echo "🤖 API Aggregator - MCP Server Mode" >&2
echo "====================================" >&2

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..." >&2
    source venv/bin/activate
fi

# Set MCP mode
export MCP_SERVER_MODE=mcp

# Load environment variables from .env file if it exists and keys aren't already set
if [ -f .env ]; then
    echo "Loading additional variables from .env file..." >&2
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "No .env file found, using environment variables from shell..." >&2
fi

# Check API keys
has_api_keys=false

if [ -n "$OPENWEATHER_API_KEY" ] && [ "$OPENWEATHER_API_KEY" != '${OPENWEATHER_API_KEY}' ]; then
    echo "✅ OpenWeatherMap API key found" >&2
    has_api_keys=true
else
    echo "❌ OpenWeatherMap API key missing or invalid" >&2
fi

if [ -n "$NEWS_API_KEY" ] && [ "$NEWS_API_KEY" != '${NEWS_API_KEY}' ]; then
    echo "✅ News API key found" >&2
    has_api_keys=true
else
    echo "❌ News API key missing or invalid" >&2
fi

if [ -n "$ALPHA_VANTAGE_API_KEY" ] && [ "$ALPHA_VANTAGE_API_KEY" != '${ALPHA_VANTAGE_API_KEY}' ]; then
    echo "✅ Alpha Vantage API key found" >&2
    has_api_keys=true
else
    echo "❌ Alpha Vantage API key missing or invalid" >&2
fi

# Exit if no valid API keys are found
if [ "$has_api_keys" = false ]; then
    echo "" >&2
    echo "❌ ERROR: No valid API keys found!" >&2
    echo "" >&2
    echo "The MCP server requires at least one valid API key to register tools." >&2
    echo "Please set environment variables in your shell (zshrc) or .env file:" >&2
    echo "" >&2
    echo "Option 1 - Add to ~/.zshrc:" >&2
    echo "  export OPENWEATHER_API_KEY=your_api_key" >&2
    echo "  export NEWS_API_KEY=your_api_key" >&2
    echo "  export ALPHA_VANTAGE_API_KEY=your_api_key" >&2
    echo "" >&2
    echo "Option 2 - Create .env file with:" >&2
    echo "  OPENWEATHER_API_KEY=your_api_key" >&2
    echo "  NEWS_API_KEY=your_api_key" >&2
    echo "  ALPHA_VANTAGE_API_KEY=your_api_key" >&2
    echo "" >&2
    echo "Get API keys from:" >&2
    echo "  • OpenWeatherMap: https://openweathermap.org/api" >&2
    echo "  • News API: https://newsapi.org/" >&2
    echo "  • Alpha Vantage: https://www.alphavantage.co/support/#api-key" >&2
    echo "" >&2
    exit 1
fi

echo "" >&2
echo "🤖 Starting MCP server for AI clients..." >&2
echo "Ready for MCP client connections (stdio mode)" >&2
echo "" >&2

# Run the MCP server - stdout will be JSON-RPC, stderr will be diagnostics
python -m src.main --mcp 