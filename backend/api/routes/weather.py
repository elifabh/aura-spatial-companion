"""
Weather API — Met Éireann + pvlib integration.
Provides local weather context and sun position data
for spatial recommendations.
"""

from fastapi import APIRouter

from backend.services.weather import get_current_weather
from backend.services.sun import get_sun_position

router = APIRouter()


@router.get("/current")
async def current_weather(lat: float = 53.3498, lon: float = -6.2603):
    """
    Get current weather from Met Éireann.
    Default coordinates: Dublin, Ireland.
    """
    weather = await get_current_weather(lat, lon)
    return weather


@router.get("/sun")
async def sun_position(lat: float = 53.3498, lon: float = -6.2603):
    """
    Get current sun position (altitude, azimuth)
    using pvlib for natural light recommendations.
    """
    position = get_sun_position(lat, lon)
    return position
