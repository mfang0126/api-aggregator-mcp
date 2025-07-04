"""FastMCP-based API Aggregator Server."""

import os
import sys
import aiohttp
import structlog
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastmcp import FastMCP, Context

from .utils.config import get_settings, validate_api_keys
from .utils.errors import APIError, ErrorCode


# Configure structlog to output to stderr
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)

# Configure logging
logger = structlog.get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("API Aggregator")

# Get settings and validate API keys at module level
settings = get_settings()
available_apis = validate_api_keys()

logger.info("API key validation", available_apis=available_apis)


@mcp.tool
async def get_weather(
    city: str,
    country: Optional[str] = None,
    units: str = "metric",
    ctx: Context = None,
) -> str:
    """
    Get current weather information for a specified city.
    
    Args:
        city: City name (required)
        country: Country code (optional, improves accuracy) 
        units: Temperature units - metric, imperial, or kelvin (default: metric)
    
    Returns:
        Current weather information as formatted text
    """
    if not available_apis["weather"]:
        return "❌ Weather tool unavailable: Missing OpenWeatherMap API key"
    
    if ctx:
        await ctx.info(f"Fetching weather for {city}...")
    
    # Validate inputs
    if not city or not city.strip():
        return "❌ Error: City name cannot be empty"
    
    if units not in ["metric", "imperial", "kelvin"]:
        return "❌ Error: Units must be one of: metric, imperial, kelvin"
    
    # Build location query
    location = city.strip()
    if country:
        location = f"{location},{country.strip()}"
    
    # Prepare API request
    params = {
        "q": location,
        "appid": settings.openweather_api_key,
        "units": units,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return _format_weather_response(data, units)
                elif response.status == 401:
                    return "❌ Error: Invalid OpenWeatherMap API key"
                elif response.status == 404:
                    return f"❌ Error: City '{location}' not found"
                else:
                    return f"❌ Error: OpenWeatherMap API error (status: {response.status})"
                    
    except Exception as e:
        logger.error("Weather API error", error=str(e))
        return f"❌ Error fetching weather data: {str(e)}"


@mcp.tool
async def get_news(
    query: Optional[str] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    page_size: int = 5,
    ctx: Context = None,
) -> str:
    """
    Get latest news headlines by topic, category, or country.
    
    Args:
        query: Search query for specific topics (optional)
        category: News category - business, entertainment, general, health, science, sports, technology (optional)
        country: Country code for country-specific news like 'us', 'gb', 'ca' (optional)
        page_size: Number of articles to return, 1-20 (default: 5)
    
    Returns:
        Latest news headlines as formatted text
    """
    if not available_apis["news"]:
        return "❌ News tool unavailable: Missing News API key"
    
    if ctx:
        await ctx.info("Fetching latest news...")
    
    # Validate inputs
    if page_size < 1 or page_size > 20:
        return "❌ Error: Page size must be between 1 and 20"
    
    valid_categories = [
        "business", "entertainment", "general", "health", 
        "science", "sports", "technology"
    ]
    if category and category not in valid_categories:
        return f"❌ Error: Category must be one of: {', '.join(valid_categories)}"
    
    # Choose endpoint and build parameters
    if query:
        endpoint = "everything"
        params = {
            "q": query,
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "language": "en",
        }
    else:
        endpoint = "top-headlines"
        params = {"pageSize": page_size}
        if category:
            params["category"] = category
        if country:
            params["country"] = country
        elif not category:
            params["country"] = "us"  # Default to US if no country/category specified
    
    params["apiKey"] = settings.news_api_key
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://newsapi.org/v2/{endpoint}",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return _format_news_response(data, query, category, country)
                elif response.status == 401:
                    return "❌ Error: Invalid News API key"
                elif response.status == 429:
                    return "❌ Error: News API rate limit exceeded"
                else:
                    return f"❌ Error: News API error (status: {response.status})"
                    
    except Exception as e:
        logger.error("News API error", error=str(e))
        return f"❌ Error fetching news data: {str(e)}"


@mcp.tool
async def get_stock_price(symbol: str, ctx: Context = None) -> str:
    """
    Get current stock price and trading information for a given symbol.
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT, GOOGL)
    
    Returns:
        Current stock price and trading information as formatted text
    """
    if not available_apis["stock"]:
        return "❌ Stock tools unavailable: Missing Alpha Vantage API key"
    
    if ctx:
        await ctx.info(f"Fetching stock data for {symbol}...")
    
    # Validate input
    if not symbol or not symbol.strip():
        return "❌ Error: Stock symbol cannot be empty"
    
    symbol = symbol.strip().upper()
    
    # Prepare API request
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": settings.alpha_vantage_api_key,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.alphavantage.co/query",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return _format_stock_response(data, symbol)
                else:
                    return f"❌ Error: Alpha Vantage API error (status: {response.status})"
                    
    except Exception as e:
        logger.error("Stock API error", error=str(e), symbol=symbol)
        return f"❌ Error fetching stock data: {str(e)}"


@mcp.tool
async def search_stocks(keywords: str, ctx: Context = None) -> str:
    """
    Search for stock symbols by company name or keywords.
    
    Args:
        keywords: Search keywords (company name, symbol, etc.)
    
    Returns:
        Matching stock symbols and company information as formatted text
    """
    if not available_apis["stock"]:
        return "❌ Stock tools unavailable: Missing Alpha Vantage API key"
    
    if ctx:
        await ctx.info(f"Searching stocks for: {keywords}")
    
    # Validate input
    if not keywords or not keywords.strip():
        return "❌ Error: Search keywords cannot be empty"
    
    params = {
        "function": "SYMBOL_SEARCH",
        "keywords": keywords.strip(),
        "apikey": settings.alpha_vantage_api_key,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.alphavantage.co/query",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return _format_search_response(data, keywords)
                else:
                    return f"❌ Error: Alpha Vantage API error (status: {response.status})"
                    
    except Exception as e:
        logger.error("Stock search API error", error=str(e), keywords=keywords)
        return f"❌ Error searching stocks: {str(e)}"


def _format_weather_response(data: Dict[str, Any], units: str) -> str:
    """Format weather API response into readable text."""
    # Unit symbols
    temp_unit = {
        "metric": "°C",
        "imperial": "°F", 
        "kelvin": "K",
    }[units]
    
    speed_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
    
    location = f"{data['name']}, {data['sys']['country']}"
    condition = data['weather'][0]['description'].title()
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    
    return f"""🌤️ Weather for {location}

📍 Condition: {condition}
🌡️ Temperature: {temp}{temp_unit} (feels like {feels_like}{temp_unit})
💧 Humidity: {humidity}%
💨 Wind Speed: {wind_speed} {speed_unit}
📊 Pressure: {data['main']['pressure']} hPa
☁️ Cloudiness: {data['clouds']['all']}%

Data from OpenWeatherMap"""


def _format_news_response(data: Dict[str, Any], query: Optional[str], category: Optional[str], country: Optional[str]) -> str:
    """Format news API response into readable text."""
    articles = data.get("articles", [])
    total_results = data.get("totalResults", 0)
    
    # Build query info
    query_parts = []
    if query:
        query_parts.append(f"Query: {query}")
    if category:
        query_parts.append(f"Category: {category}")
    if country:
        query_parts.append(f"Country: {country}")
    
    query_info = " | ".join(query_parts) if query_parts else "Top Headlines"
    
    result = f"📰 Latest News ({query_info})\n"
    result += f"Found {total_results} articles, showing {len(articles)}:\n\n"
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "No title")
        source = article.get("source", {}).get("name", "Unknown")
        description = article.get("description", "No description available")
        url = article.get("url", "")
        
        # Parse publication date
        published_at = article.get("publishedAt", "Unknown time")
        if published_at != "Unknown time":
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                published_at = dt.strftime("%Y-%m-%d %H:%M UTC")
            except:
                pass
        
        result += f"{i}. **{title}**\n"
        result += f"   📰 Source: {source} | 📅 {published_at}\n"
        result += f"   📝 {description}\n"
        if url:
            result += f"   🔗 {url}\n"
        result += "\n"
    
    return result


def _format_stock_response(data: Dict[str, Any], symbol: str) -> str:
    """Format stock API response into readable text."""
    # Check for API errors
    if "Error Message" in data:
        return f"❌ Error: Invalid stock symbol '{symbol}'"
    
    if "Note" in data:
        return "❌ Error: Alpha Vantage API rate limit exceeded"
    
    quote = data.get("Global Quote", {})
    if not quote:
        return f"❌ Error: No data available for symbol '{symbol}'"
    
    # Extract quote data
    current_price = float(quote.get("05. price", 0))
    previous_close = float(quote.get("08. previous close", 0))
    change = float(quote.get("09. change", 0))
    change_percent = quote.get("10. change percent", "0%").replace("%", "")
    open_price = float(quote.get("02. open", 0))
    high = float(quote.get("03. high", 0))
    low = float(quote.get("04. low", 0))
    volume = int(quote.get("06. volume", 0))
    trading_day = quote.get("07. latest trading day", "Unknown")
    
    # Determine if stock is up or down
    direction = "📈" if change >= 0 else "📉"
    
    return f"""📊 Stock Quote for {symbol}

💰 Current Price: ${current_price:.2f}
{direction} Change: ${change:+.2f} ({change_percent:+}%)
📅 Previous Close: ${previous_close:.2f}

📈 Day's Trading:
   🔓 Open: ${open_price:.2f}
   ⬆️ High: ${high:.2f}
   ⬇️ Low: ${low:.2f}
   📊 Volume: {volume:,}

📅 Last Trading Day: {trading_day}
Data from Alpha Vantage"""


def _format_search_response(data: Dict[str, Any], keywords: str) -> str:
    """Format stock search API response into readable text."""
    # Check for API errors
    if "Error Message" in data:
        return f"❌ Error: {data['Error Message']}"
    
    if "Note" in data:
        return "❌ Error: Alpha Vantage API rate limit exceeded"
    
    matches = data.get("bestMatches", [])
    if not matches:
        return f"❌ No stocks found matching '{keywords}'"
    
    result = f"🔍 Stock Search Results for '{keywords}':\n\n"
    
    for i, match in enumerate(matches[:10], 1):  # Limit to top 10 results
        symbol = match.get("1. symbol", "N/A")
        name = match.get("2. name", "N/A")
        type_desc = match.get("3. type", "N/A")
        region = match.get("4. region", "N/A")
        currency = match.get("8. currency", "N/A")
        
        result += f"{i}. **{symbol}** - {name}\n"
        result += f"   🏢 Type: {type_desc}\n"
        result += f"   🌍 Region: {region} | 💱 Currency: {currency}\n\n"
    
    return result


def get_fastmcp_server() -> FastMCP:
    """Get the configured FastMCP server instance."""
    return mcp 