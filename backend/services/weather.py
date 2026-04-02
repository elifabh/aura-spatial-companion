"""
Weather Service — Met Éireann API integration.
Fetches real-time Irish weather data for spatial recommendations.
Free, no API key required.
"""

import httpx
from backend.config import MET_EIREANN_API_URL


async def get_current_weather(lat: float, lon: float) -> dict:
    """
    Fetch current weather observations from Met Éireann.
    Falls back to a default response if the API is unreachable.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                MET_EIREANN_API_URL,
                params={"lat": lat, "lon": lon},
            )
            response.raise_for_status()
            data = response.json()

            return {
                "temperature": data.get("temperature"),
                "humidity": data.get("humidity"),
                "wind_speed": data.get("windSpeed"),
                "weather_description": data.get("weatherDescription", ""),
                "rain": data.get("rainfall", 0),
                "source": "met_eireann",
            }
    except Exception:
        return {
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
            "weather_description": "Weather data unavailable",
            "rain": None,
            "source": "fallback",
        }
