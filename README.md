# API Aggregator MCP Server

A **Model Context Protocol (MCP) Server** that provides unified access to multiple external APIs through a single, consistent interface. Built for AI agents and LLMs, this server aggregates weather, news, and financial data into standardized tool calls.

## Features

- ✅ **MCP Protocol Compliant**: Full JSON-RPC 2.0 support with proper tool discovery
- ✅ **Multiple API Integrations**: Weather, news, and stock market data
- ✅ **Unified Error Handling**: Consistent error responses across all APIs  
- ✅ **Type-Safe**: Full type hints and Pydantic validation
- ✅ **Async Support**: High-performance async/await throughout
- ✅ **Structured Logging**: Rich, structured logs for monitoring
- ✅ **Environment-Based Config**: Secure API key management

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd api-aggregator-mcp

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your API keys:

```env
# Required for weather data
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Required for news data  
NEWS_API_KEY=your_news_api_key_here

# Required for stock data
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Optional server configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_SERVER_DEBUG=true
LOG_LEVEL=INFO
```

### 3. Get API Keys

- **OpenWeatherMap**: [Get free API key](https://openweathermap.org/api)
- **News API**: [Get free API key](https://newsapi.org/)
- **Alpha Vantage**: [Get free API key](https://www.alphavantage.co/support/#api-key)

### 4. Run the Server

```bash
python -m src.main
```

The server will start at `http://localhost:8000`

## Available Tools

### 🌤️ Weather Tool: `get_weather`

Get current weather information for any city.

**Parameters:**
- `city` (required): City name
- `country` (optional): Country code (e.g., "US", "GB")  
- `units` (optional): Temperature units - "metric" (default), "imperial", or "kelvin"

**Example:**
```json
{
  "city": "London",
  "country": "GB",
  "units": "metric"
}
```

**Response:**
```json
{
  "location": {
    "city": "London",
    "country": "GB",
    "coordinates": {"latitude": 51.5074, "longitude": -0.1278}
  },
  "weather": {
    "condition": "Clouds",
    "description": "overcast clouds"
  },
  "temperature": {
    "current": 15.2,
    "feels_like": 14.8,
    "unit": "°C"
  },
  "humidity": "73%",
  "wind": {"speed": "3.5 m/s", "direction": "240°"}
}
```

### 📰 News Tool: `get_news` (Coming Soon)

Get latest news headlines by topic or region.

### 📈 Stock Tool: `get_stock_price` (Coming Soon)

Get current stock prices and financial data.

## API Endpoints

### Health Check
```
GET /
```

### List Available Tools
```
GET /tools
```

### Invoke Tool (REST)
```
POST /tools/{tool_name}
Content-Type: application/json

{
  "city": "New York",
  "units": "imperial"
}
```

### MCP Protocol Endpoint
```
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "city": "Tokyo",
      "country": "JP"
    }
  },
  "id": "1"
}
```

## Development

### Project Structure

```
api-aggregator-mcp/
├── src/
│   ├── main.py           # Application entry point
│   ├── server.py         # MCP server implementation  
│   ├── tools/            # API tool implementations
│   │   ├── weather.py    # Weather API integration
│   │   ├── news.py       # News API integration (TODO)
│   │   └── stock.py      # Stock API integration (TODO)
│   └── utils/
│       ├── config.py     # Configuration management
│       └── errors.py     # Error handling utilities
├── tests/                # Unit tests
├── requirements.txt      # Dependencies
└── README.md            # This file
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code  
flake8 src/

# Type checking
mypy src/
```

### Adding New Tools

1. Create a new file in `src/tools/`
2. Implement the service class and handler function
3. Define the tool schema
4. Register in `src/main.py`

Example tool template:

```python
# src/tools/example.py
async def example_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for example tool."""
    # Validate parameters
    # Call external API
    # Return normalized data
    pass

EXAMPLE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "param1": {"type": "string", "description": "..."},
    },
    "required": ["param1"],
}
```

## Error Handling

All errors are returned in JSON-RPC format:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "API key missing for OpenWeatherMap",
    "data": {"api": "OpenWeatherMap"}
  },
  "id": "1"
}
```

Common error codes:
- `-32001`: API key missing
- `-32002`: API key invalid  
- `-32003`: External API error
- `-32004`: Rate limit exceeded
- `-32602`: Invalid parameters

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 