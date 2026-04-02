"""
Sun Position Service — pvlib integration.
Calculates solar position for natural light recommendations.
Runs entirely locally, no API calls.
"""

from datetime import datetime, timezone
import pvlib


def get_sun_position(lat: float, lon: float) -> dict:
    """
    Calculate the current sun position (altitude, azimuth)
    for the given coordinates using pvlib.
    """
    try:
        now = datetime.now(timezone.utc)
        location = pvlib.location.Location(latitude=lat, longitude=lon)
        solar_position = location.get_solarposition(now)

        altitude = float(solar_position["apparent_elevation"].iloc[0])
        azimuth = float(solar_position["azimuth"].iloc[0])

        # Determine light quality
        if altitude < 0:
            light_quality = "night"
        elif altitude < 10:
            light_quality = "twilight"
        elif altitude < 30:
            light_quality = "low_angle"
        else:
            light_quality = "good"

        return {
            "altitude": round(altitude, 2),
            "azimuth": round(azimuth, 2),
            "light_quality": light_quality,
            "timestamp": now.isoformat(),
            "is_daylight": altitude > 0,
        }
    except Exception as e:
        return {
            "altitude": None,
            "azimuth": None,
            "light_quality": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_daylight": None,
            "error": str(e),
        }
