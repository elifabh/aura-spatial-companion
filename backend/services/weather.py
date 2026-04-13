"""
Weather Service — Met Éireann API integration.
Fetches real-time Irish weather data for spatial recommendations.
Free, no API key required.
"""

import httpx
from backend.config import MET_EIREANN_API_URL


async def get_current_weather(lat: float, lon: float) -> dict:
    """
    Fetch current weather observations from Open-Meteo.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,rain,weather_code,wind_speed_10m"
                },
            )
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            
            # Basic WMO weather code mapping to string
            wmo = current.get("weather_code", 0)
            desc = "Clear"
            if wmo in [1, 2, 3]: desc = "Cloudy"
            elif wmo in [45, 48]: desc = "Fog"
            elif 50 <= wmo <= 69: desc = "Rain"
            elif 70 <= wmo <= 79: desc = "Snow"
            elif 80 <= wmo <= 99: desc = "Showers/Storm"

            return {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "weather_description": desc,
                "rain": current.get("rain", 0),
                "source": "open_meteo",
            }
    except Exception as e:
        print(f"[Aura] Weather API error: {e}")
        return {
            "temperature": None,
            "humidity": None,
            "wind_speed": None,
            "weather_description": "Weather data unavailable",
            "rain": None,
            "source": "fallback",
        }
