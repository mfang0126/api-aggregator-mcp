# API Aggregator MCP Server (FastMCP)

A production-ready **Model Context Protocol (MCP) Server** built with [FastMCP](https://github.com/jlowin/fastmcp) that provides unified access to weather, news, and financial APIs through a single, standards-compliant interface. Built for AI agents and LLMs with full MCP protocol compliance.

## 🚀 **Dual-Mode Server: MCP + REST API**

**One server, two interfaces** - built with [FastMCP](https://github.com/jlowin/fastmcp):

### 🤖 **MCP Mode** (for AI clients)
- **Use with**: Cursor IDE, Claude Desktop, MCP clients
- **Transport**: stdio (JSON-RPC over standard input/output)
- **Start with**: `python -m src.main --mcp`

### 🌐 **REST API Mode** (for web clients)  
- **Use with**: Web applications, curl, Postman, JavaScript
- **Transport**: HTTP with OpenAPI/Swagger docs
- **Start with**: `python -m src.main --api`
- **Access**: `http://localhost:8000` with interactive docs at `/docs`

### ✨ **Benefits of FastMCP Implementation:**
- ✅ **500+ lines reduced to ~400 lines** using decorator patterns
- ✅ **No manual JSON-RPC handling** - FastMCP manages protocols
- ✅ **Type-safe tool definitions** with automatic schema generation
- ✅ **Single codebase** serves both MCP and REST API clients
- ✅ **Built-in validation** and error handling

## 🎯 **Status: FULLY WORKING** ✅

**All 4 tools tested and operational:**
- 🌤️ **Weather Tool**: Real-time weather data (OpenWeatherMap)
- 📰 **News Tool**: Latest headlines by topic/category (News API)  
- 📈 **Stock Price Tool**: Live stock quotes (Alpha Vantage)
- 🔍 **Stock Search Tool**: Company symbol lookup (Alpha Vantage)

## Features

- ✅ **MCP Protocol Compliant**: Full JSON-RPC 2.0 support with tool discovery
- ✅ **4 Production APIs**: Weather, news, and financial data sources
- ✅ **Unified Error Handling**: Consistent JSON-RPC error responses
- ✅ **Type-Safe**: Full type hints and Pydantic validation  
- ✅ **Async Support**: High-performance async/await throughout
- ✅ **Structured Logging**: Rich, structured logs for monitoring
- ✅ **Environment-Based Config**: Secure API key management
- ✅ **Multiple Transports**: Both stdio and HTTP SSE support

## Setup

### Prerequisites
- Python 3.11+ 
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd api-aggregator-mcp
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp env_example.txt .env
   # Edit .env and add your actual API keys
   ```

5. **Get API Keys:**
   - **OpenWeatherMap:** https://openweathermap.org/api
   - **News API:** https://newsapi.org/
   - **Alpha Vantage:** https://www.alphavantage.co/support/#api-key

### Running the Server

**🚀 Dual-Mode Server - Choose Your Interface:**

**Option 1: MCP Server Mode (for AI clients like Cursor IDE):**
```bash
./run-mcp-server-only.sh           # Dedicated MCP script
# OR
python -m src.main --mcp           # Direct command
```

**Option 2: REST API Mode (for web/HTTP clients):**
```bash
./run-api-server.sh                # Dedicated API script  
# OR
python -m src.main --api --port 8000   # Direct command
```

**Option 3: Interactive Mode (choose at runtime):**
```bash
./run-mcp-server.sh                # Shows menu to choose mode
```

The server will automatically:
- ✅ Activate the virtual environment if available
- ✅ Validate API keys before starting
- ✅ Register tools only for APIs with valid keys
- ✅ Show clear error messages if no API keys are found

## Quick Start

### 1. Configuration

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
MCP_SERVER_MODE=both  # "api", "mcp", or "both"
LOG_LEVEL=INFO
```

### 4. Run the Server

```bash
python -m src.main
```
Server starts at `http://localhost:8000`

### 5. Server Modes

The server supports three operation modes via the `MCP_SERVER_MODE` environment variable:

#### API Mode (`MCP_SERVER_MODE=api`)
- **REST API endpoints only**
- Use for traditional HTTP API integration
- Available endpoints: `GET /`, `GET /tools`, `POST /tools/{tool_name}`

#### MCP Mode (`MCP_SERVER_MODE=mcp`)  
- **MCP protocol endpoint only**
- Use for direct MCP client integration (AI agents/LLMs)
- Available endpoints: `GET /`, `POST /mcp`

#### Both Mode (`MCP_SERVER_MODE=both`) - Default
- **All endpoints available**
- Maximum flexibility for different client types
- Available endpoints: `GET /`, `GET /tools`, `POST /tools/{tool_name}`, `POST /mcp`

> **✅ All modes fully tested and working!** The server correctly enables/disables endpoints based on the selected mode.

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

### 📰 News Tool: `get_news`

Get latest news headlines by topic, category, or country.

**Parameters:**
- `query` (optional): Search query for specific news
- `category` (optional): News category ("business", "entertainment", "general", "health", "science", "sports", "technology")
- `country` (optional): Country code (e.g., "us", "gb", "de")
- `page_size` (optional): Number of articles to return (default: 10, max: 100)

### 📈 Stock Tools: `get_stock_price` & `search_stocks`

Get current stock prices and search for stock symbols.

**`get_stock_price` Parameters:**
- `symbol` (required): Stock symbol (e.g., "AAPL", "MSFT", "GOOGL")

**`search_stocks` Parameters:**
- `keywords` (required): Company name or keywords to search for

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
│   │   ├── news.py       # News API integration  
│   │   └── stock.py      # Stock API integration
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