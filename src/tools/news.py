"""News API tool implementation."""

import aiohttp
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.config import get_settings
from ..utils.errors import (
    APIError,
    ErrorCode,
    handle_external_api_error,
    create_missing_api_key_error,
    create_validation_error,
)


logger = structlog.get_logger(__name__)


class NewsService:
    """Service for fetching news data from News API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://newsapi.org/v2"
    
    async def get_news(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        country: Optional[str] = None,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Get latest news headlines.
        
        Args:
            query: Search query for specific topics
            category: News category (business, entertainment, general, health, science, sports, technology)
            country: Country code for country-specific news (us, gb, ca, etc.)
            page_size: Number of articles to return (1-100)
        
        Returns:
            News data dictionary
        """
        if not self.settings.news_api_key:
            raise create_missing_api_key_error("News API")
        
        # Validate inputs
        if page_size < 1 or page_size > 100:
            raise create_validation_error(
                "page_size",
                page_size,
                "Page size must be between 1 and 100"
            )
        
        valid_categories = [
            "business", "entertainment", "general", "health", 
            "science", "sports", "technology"
        ]
        if category and category not in valid_categories:
            raise create_validation_error(
                "category",
                category,
                f"Category must be one of: {', '.join(valid_categories)}"
            )
        
        # Choose endpoint based on parameters
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
            params = {
                "pageSize": page_size,
            }
            if category:
                params["category"] = category
            if country:
                params["country"] = country
            elif not category:  # Default to US if no country or category specified
                params["country"] = "us"
        
        params["apiKey"] = self.settings.news_api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{endpoint}",
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_news_data(data, query, category, country)
                    elif response.status == 401:
                        raise APIError(
                            message="Invalid News API key",
                            code=ErrorCode.API_KEY_INVALID,
                            data={"api": "News API"},
                        )
                    elif response.status == 429:
                        raise APIError(
                            message="News API rate limit exceeded",
                            code=ErrorCode.RATE_LIMIT_EXCEEDED,
                            data={"api": "News API"},
                        )
                    else:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        raise APIError(
                            message=f"News API error: {response.status}",
                            code=ErrorCode.EXTERNAL_API_ERROR,
                            data={
                                "status_code": response.status,
                                "response": error_data,
                            },
                        )
        
        except aiohttp.ClientError as e:
            raise handle_external_api_error(e, "News API", "get_news")
        except APIError:
            raise
        except Exception as e:
            raise handle_external_api_error(e, "News API", "get_news")
    
    def _normalize_news_data(
        self, 
        data: Dict[str, Any], 
        query: Optional[str], 
        category: Optional[str], 
        country: Optional[str]
    ) -> Dict[str, Any]:
        """Normalize News API response into our standard format."""
        articles = []
        
        for article in data.get("articles", []):
            # Parse publication date
            published_at = article.get("publishedAt")
            if published_at:
                try:
                    published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    formatted_date = published_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    formatted_date = published_at
            else:
                formatted_date = "Unknown"
            
            normalized_article = {
                "title": article.get("title", "No title"),
                "description": article.get("description", "No description available"),
                "url": article.get("url"),
                "source": {
                    "name": article.get("source", {}).get("name", "Unknown"),
                    "id": article.get("source", {}).get("id"),
                },
                "author": article.get("author", "Unknown"),
                "published_at": formatted_date,
                "url_to_image": article.get("urlToImage"),
            }
            articles.append(normalized_article)
        
        return {
            "query_info": {
                "search_query": query,
                "category": category,
                "country": country,
                "total_results": data.get("totalResults", 0),
                "articles_returned": len(articles),
            },
            "articles": articles,
            "source": "News API",
            "retrieved_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }


# Initialize service instance
news_service = NewsService()


async def get_news_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for the get_news tool.
    
    Args:
        parameters: Tool parameters containing query, category, country, and page_size
    
    Returns:
        Normalized news data
    """
    logger.info("Processing news request", parameters=parameters)
    
    query = parameters.get("query")
    category = parameters.get("category")
    country = parameters.get("country")
    page_size = parameters.get("page_size", 10)
    
    result = await news_service.get_news(
        query=query,
        category=category,
        country=country,
        page_size=page_size,
    )
    
    logger.info("News request completed", 
               query=query, category=category, country=country, 
               articles_count=len(result["articles"]))
    return result


# Tool schema for registration
NEWS_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query for specific news topics (optional)",
        },
        "category": {
            "type": "string",
            "description": "News category (optional)",
            "enum": ["business", "entertainment", "general", "health", "science", "sports", "technology"],
        },
        "country": {
            "type": "string",
            "description": "Country code for country-specific news (e.g., 'us', 'gb', 'ca')",
            "pattern": "^[a-z]{2}$",
        },
        "page_size": {
            "type": "integer",
            "description": "Number of articles to return (1-100)",
            "minimum": 1,
            "maximum": 100,
            "default": 10,
        },
    },
    "additionalProperties": False,
} 