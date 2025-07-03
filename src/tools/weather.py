"""Weather API tool implementation."""

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


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(
        self,
        city: str,
        country: Optional[str] = None,
        units: str = "metric",
    ) -> Dict[str, Any]:
        """
        Get current weather for a city.
        
        Args:
            city: City name
            country: Country code (optional, improves accuracy)
            units: Temperature units (metric, imperial, kelvin)
        
        Returns:
            Weather data dictionary
        """
        if not self.settings.openweather_api_key:
            raise create_missing_api_key_error("OpenWeatherMap")
        
        # Validate inputs
        if not city or not city.strip():
            raise create_validation_error(
                "city",
                city,
                "City name cannot be empty"
            )
        
        if units not in ["metric", "imperial", "kelvin"]:
            raise create_validation_error(
                "units",
                units,
                "Units must be one of: metric, imperial, kelvin"
            )
        
        # Build location query
        location = city.strip()
        if country:
            location = f"{location},{country.strip()}"
        
        # Prepare API request
        params = {
            "q": location,
            "appid": self.settings.openweather_api_key,
            "units": units,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/weather",
                    params=params,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._normalize_weather_data(data, units)
                    elif response.status == 401:
                        raise APIError(
                            message="Invalid OpenWeatherMap API key",
                            code=ErrorCode.API_KEY_INVALID,
                            data={"api": "OpenWeatherMap"},
                        )
                    elif response.status == 404:
                        raise APIError(
                            message=f"City '{location}' not found",
                            code=ErrorCode.INVALID_PARAMS,
                            data={"city": location},
                        )
                    else:
                        error_text = await response.text()
                        raise APIError(
                            message=f"OpenWeatherMap API error: {response.status}",
                            code=ErrorCode.EXTERNAL_API_ERROR,
                            data={
                                "status_code": response.status,
                                "response": error_text,
                            },
                        )
        
        except aiohttp.ClientError as e:
            raise handle_external_api_error(e, "OpenWeatherMap", "get_weather")
        except APIError:
            raise
        except Exception as e:
            raise handle_external_api_error(e, "OpenWeatherMap", "get_weather")
    
    def _normalize_weather_data(self, data: Dict[str, Any], units: str) -> Dict[str, Any]:
        """Normalize OpenWeatherMap response into our standard format."""
        # Unit symbols
        temp_unit = {
            "metric": "°C",
            "imperial": "°F",
            "kelvin": "K",
        }[units]
        
        speed_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
        
        return {
            "location": {
                "city": data["name"],
                "country": data["sys"]["country"],
                "coordinates": {
                    "latitude": data["coord"]["lat"],
                    "longitude": data["coord"]["lon"],
                },
            },
            "weather": {
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
            },
            "temperature": {
                "current": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "min": data["main"]["temp_min"],
                "max": data["main"]["temp_max"],
                "unit": temp_unit,
            },
            "humidity": f"{data['main']['humidity']}%",
            "pressure": f"{data['main']['pressure']} hPa",
            "visibility": f"{data.get('visibility', 0) / 1000:.1f} km",
            "wind": {
                "speed": f"{data['wind']['speed']} {speed_unit}",
                "direction": f"{data['wind'].get('deg', 0)}°",
            },
            "clouds": f"{data['clouds']['all']}%",
            "timestamp": data["dt"],
            "timezone": data["timezone"],
            "source": "OpenWeatherMap",
        }


# Initialize service instance
weather_service = WeatherService()


async def get_weather_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for the get_weather tool.
    
    Args:
        parameters: Tool parameters containing city, country, and units
    
    Returns:
        Normalized weather data
    """
    logger.info("Processing weather request", parameters=parameters)
    
    city = parameters.get("city")
    country = parameters.get("country")
    units = parameters.get("units", "metric")
    
    if not city:
        raise create_validation_error(
            "city",
            city,
            "City parameter is required"
        )
    
    result = await weather_service.get_current_weather(
        city=city,
        country=country,
        units=units,
    )
    
    logger.info("Weather request completed", city=city, country=country)
    return result


# Tool schema for registration
WEATHER_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "Name of the city",
            "minLength": 1,
        },
        "country": {
            "type": "string",
            "description": "Country code (optional, e.g., 'US', 'GB')",
            "pattern": "^[A-Z]{2}$",
        },
        "units": {
            "type": "string",
            "description": "Temperature units",
            "enum": ["metric", "imperial", "kelvin"],
            "default": "metric",
        },
    },
    "required": ["city"],
    "additionalProperties": False,
} 