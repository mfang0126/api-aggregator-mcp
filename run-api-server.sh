#!/bin/bash

# API Aggregator - REST API Server Mode
# Runs the server as a web API accessible via HTTP

trap "echo -e '\n🛑 Server stopped by user (Ctrl+C)'; exit 0" SIGINT

echo "🌐 API Aggregator - REST API Mode"
echo "================================="

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading additional variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "No .env file found, using environment variables from shell..."
fi

# Set server mode to API
export SERVER_MODE=api

# Check API keys (same validation as MCP mode)
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
    echo "The API server requires at least one valid API key to serve endpoints."
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

PORT=${MCP_SERVER_PORT:-8000}
HOST=${MCP_SERVER_HOST:-127.0.0.1}

echo ""
echo "🌐 Starting REST API server..."
echo "📍 Server URL: http://$HOST:$PORT"
echo "📚 API Documentation: http://$HOST:$PORT/docs"
echo "🔄 Interactive API: http://$HOST:$PORT/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the API server
python -m src.main --api --host $HOST --port $PORT 