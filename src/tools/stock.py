"""Stock market data API tool implementation."""

import aiohttp
import structlog
from typing import Dict, Any, Optional

from ..utils.config import get_settings
from ..utils.errors import (
    APIError,
    ErrorCode,
    handle_external_api_error,
    create_missing_api_key_error,
    create_validation_error,
)


logger = structlog.get_logger(__name__)


class StockService:
    """Service for fetching stock data from Alpha Vantage API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://www.alphavantage.co/query"
    
    async def get_stock_quote(
        self,
        symbol: str,
        include_extended: bool = False,
    ) -> Dict[str, Any]:
        """
        Get current stock quote for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., AAPL, MSFT, GOOGL)
            include_extended: Include extended trading hours data
        
        Returns:
            Stock data dictionary
        """
        if not self.settings.alpha_vantage_api_key:
            raise create_missing_api_key_error("Alpha Vantage")
        
        # Validate inputs
        if not symbol or not symbol.strip():
            raise create_validation_error(
                "symbol",
                symbol,
                "Stock symbol cannot be empty"
            )
        
        symbol = symbol.strip().upper()
        
        # Prepare API request
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.settings.alpha_vantage_api_key,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_stock_data(data, symbol)
                    else:
                        error_text = await response.text()
                        raise APIError(
                            message=f"Alpha Vantage API error: {response.status}",
                            code=ErrorCode.EXTERNAL_API_ERROR,
                            data={
                                "status_code": response.status,
                                "response": error_text,
                            },
                        )
        
        except aiohttp.ClientError as e:
            raise handle_external_api_error(e, "Alpha Vantage", "get_stock_quote")
        except APIError:
            raise
        except Exception as e:
            raise handle_external_api_error(e, "Alpha Vantage", "get_stock_quote")
    
    async def get_stock_search(self, keywords: str) -> Dict[str, Any]:
        """
        Search for stock symbols by company name or keywords.
        
        Args:
            keywords: Search keywords (company name, symbol, etc.)
        
        Returns:
            Search results with matching symbols
        """
        if not self.settings.alpha_vantage_api_key:
            raise create_missing_api_key_error("Alpha Vantage")
        
        if not keywords or not keywords.strip():
            raise create_validation_error(
                "keywords",
                keywords,
                "Search keywords cannot be empty"
            )
        
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords.strip(),
            "apikey": self.settings.alpha_vantage_api_key,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_search_data(data, keywords)
                    else:
                        error_text = await response.text()
                        raise APIError(
                            message=f"Alpha Vantage API error: {response.status}",
                            code=ErrorCode.EXTERNAL_API_ERROR,
                            data={
                                "status_code": response.status,
                                "response": error_text,
                            },
                        )
        
        except aiohttp.ClientError as e:
            raise handle_external_api_error(e, "Alpha Vantage", "get_stock_search")
        except APIError:
            raise
        except Exception as e:
            raise handle_external_api_error(e, "Alpha Vantage", "get_stock_search")
    
    def _normalize_stock_data(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Normalize Alpha Vantage stock quote response."""
        # Check for API errors
        if "Error Message" in data:
            raise APIError(
                message=f"Invalid stock symbol: {symbol}",
                code=ErrorCode.INVALID_PARAMS,
                data={"symbol": symbol, "error": data["Error Message"]},
            )
        
        if "Note" in data:
            raise APIError(
                message="Alpha Vantage API rate limit exceeded",
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                data={"api": "Alpha Vantage"},
            )
        
        quote = data.get("Global Quote", {})
        if not quote:
            raise APIError(
                message=f"No data available for symbol: {symbol}",
                code=ErrorCode.EXTERNAL_API_ERROR,
                data={"symbol": symbol},
            )
        
        # Extract quote data
        current_price = float(quote.get("05. price", 0))
        previous_close = float(quote.get("08. previous close", 0))
        change = float(quote.get("09. change", 0))
        change_percent = quote.get("10. change percent", "0%").replace("%", "")
        
        return {
            "symbol": quote.get("01. symbol", symbol),
            "price": {
                "current": current_price,
                "previous_close": previous_close,
                "change": change,
                "change_percent": f"{change_percent}%",
                "currency": "USD",
            },
            "trading": {
                "open": float(quote.get("02. open", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "volume": int(quote.get("06. volume", 0)),
            },
            "last_trading_day": quote.get("07. latest trading day", "Unknown"),
            "source": "Alpha Vantage",
        }
    
    def _normalize_search_data(self, data: Dict[str, Any], keywords: str) -> Dict[str, Any]:
        """Normalize Alpha Vantage symbol search response."""
        # Check for API errors
        if "Error Message" in data:
            raise APIError(
                message=f"Search error: {data['Error Message']}",
                code=ErrorCode.EXTERNAL_API_ERROR,
                data={"keywords": keywords},
            )
        
        if "Note" in data:
            raise APIError(
                message="Alpha Vantage API rate limit exceeded",
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                data={"api": "Alpha Vantage"},
            )
        
        matches = data.get("bestMatches", [])
        results = []
        
        for match in matches:
            results.append({
                "symbol": match.get("1. symbol", ""),
                "name": match.get("2. name", ""),
                "type": match.get("3. type", ""),
                "region": match.get("4. region", ""),
                "market_open": match.get("5. marketOpen", ""),
                "market_close": match.get("6. marketClose", ""),
                "timezone": match.get("7. timezone", ""),
                "currency": match.get("8. currency", ""),
                "match_score": float(match.get("9. matchScore", 0)),
            })
        
        return {
            "search_keywords": keywords,
            "total_matches": len(results),
            "matches": results,
            "source": "Alpha Vantage",
        }


# Initialize service instance
stock_service = StockService()


async def get_stock_price_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for the get_stock_price tool.
    
    Args:
        parameters: Tool parameters containing symbol
    
    Returns:
        Normalized stock data
    """
    logger.info("Processing stock quote request", parameters=parameters)
    
    symbol = parameters.get("symbol")
    
    if not symbol:
        raise create_validation_error(
            "symbol",
            symbol,
            "Stock symbol parameter is required"
        )
    
    result = await stock_service.get_stock_quote(symbol=symbol)
    
    logger.info("Stock quote request completed", symbol=symbol)
    return result


async def search_stocks_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for the search_stocks tool.
    
    Args:
        parameters: Tool parameters containing keywords
    
    Returns:
        Stock search results
    """
    logger.info("Processing stock search request", parameters=parameters)
    
    keywords = parameters.get("keywords")
    
    if not keywords:
        raise create_validation_error(
            "keywords",
            keywords,
            "Search keywords parameter is required"
        )
    
    result = await stock_service.get_stock_search(keywords=keywords)
    
    logger.info("Stock search request completed", keywords=keywords, matches=len(result["matches"]))
    return result


# Tool schemas for registration
STOCK_PRICE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "symbol": {
            "type": "string",
            "description": "Stock symbol (e.g., AAPL, MSFT, GOOGL)",
            "minLength": 1,
            "pattern": "^[A-Za-z0-9.-]+$",
        },
    },
    "required": ["symbol"],
    "additionalProperties": False,
}

STOCK_SEARCH_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "string",
            "description": "Search keywords (company name, symbol, etc.)",
            "minLength": 1,
        },
    },
    "required": ["keywords"],
    "additionalProperties": False,
} 