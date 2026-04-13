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


def _heading_to_direction(heading: float) -> str:
    """Convert compass heading (0-360) to cardinal direction label."""
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = round(heading / 45) % 8
    return dirs[index]


def get_optimal_position(
    lat: float, lon: float, compass_heading: float
) -> dict:
    """
    Combine compass heading with sun azimuth to determine:
    - Which direction the user/window is facing
    - Whether the sun is currently hitting this direction
    - When the sun will hit this direction today
    """
    sun = get_sun_position(lat, lon)
    if sun.get("error"):
        return {"error": sun["error"], "facing": None}

    facing = _heading_to_direction(compass_heading)
    sun_dir = _heading_to_direction(sun["azimuth"]) if sun["azimuth"] else None

    # Calculate angle difference between facing direction and sun
    angle_diff = abs(compass_heading - (sun["azimuth"] or 0))
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    # Is sun currently shining on the facing direction?
    sun_hitting = angle_diff < 60 and sun.get("is_daylight", False)

    return {
        "facing_direction": facing,
        "facing_degrees": round(compass_heading),
        "sun_azimuth": sun["azimuth"],
        "sun_altitude": sun["altitude"],
        "sun_direction": sun_dir,
        "sun_hitting_this_direction": sun_hitting,
        "angle_to_sun": round(angle_diff, 1),
        "light_quality": sun["light_quality"],
        "is_daylight": sun.get("is_daylight"),
    }


def get_sun_recommendations(
    lat: float, lon: float, compass_heading: float = None, profile: dict = None
) -> list[str]:
    """
    Generate profile-aware sun/light recommendations.
    Combines sun position, compass data, and user profile.
    """
    sun = get_sun_position(lat, lon)
    recommendations = []
    groups = []

    # Detect groups if profile available
    if profile:
        try:
            from backend.core.group_rules import detect_groups
            groups = detect_groups(profile)
        except Exception:
            pass

    # Child-specific
    if "child" in groups:
        if sun.get("is_daylight") and sun.get("light_quality") in ["good", "low_angle"]:
            recommendations.append(
                "☀️ There's good sunlight now — great time for your child to play near the window for vitamin D."
            )
        else:
            recommendations.append(
                "🌙 Not much sun right now. Tomorrow try 15-20 minutes of window-side play during daylight for vitamin D."
            )

    # SAD / dark-country
    if sun.get("light_quality") in ["twilight", "night"] or sun.get("altitude", 0) and sun["altitude"] < 15:
        recommendations.append(
            "💡 Low natural light right now. Keep indoor lights bright and warm to fight the winter blues."
        )

    # Yoga/wellness direction
    if "wellness" in groups and compass_heading is not None:
        facing = _heading_to_direction(compass_heading)
        if facing in ['E', 'NE', 'SE']:
            recommendations.append(
                f"🧘 You're facing {facing} — perfect for morning meditation! This direction catches the sunrise."
            )
        else:
            recommendations.append(
                "🧘 For morning meditation, try facing east towards the sunrise for optimal energy."
            )

    # Compass-based window analysis
    if compass_heading is not None and sun.get("azimuth"):
        pos = get_optimal_position(lat, lon, compass_heading)
        if pos.get("sun_hitting_this_direction"):
            recommendations.append(
                f"🌞 Sun is shining from the {pos['sun_direction']} direction right now. "
                f"This window (facing {pos['facing_direction']}) is getting direct light!"
            )
        elif sun.get("is_daylight"):
            recommendations.append(
                f"🪟 This window faces {pos['facing_direction']}. "
                f"Sun is currently in the {pos['sun_direction']} — "
                f"try a window facing that direction for direct light."
            )

    # General light advice
    if sun.get("is_daylight") and sun.get("altitude", 0) > 5:
        recommendations.append(
            "🌤️ There's daylight available — open those curtains and let it in!"
        )

    # Default
    if not recommendations:
        recommendations.append(
            "💡 Make the most of whatever light you have. Natural light boosts mood and focus."
        )

    return recommendations


def get_sunrise_sunset(lat: float, lon: float) -> dict:
    """Calculate sunrise and sunset times for today using pvlib."""
    try:
        from pandas import Timestamp
        import pandas as pd

        location = pvlib.location.Location(latitude=lat, longitude=lon)
        today = pd.Timestamp.now(tz="UTC").normalize()
        
        # Get sun rise/set times
        times = location.get_sun_rise_set_transit(today)

        sunrise = times["sunrise"].iloc[0]
        sunset = times["sunset"].iloc[0]
        solar_noon = times["transit"].iloc[0]

        # Golden hour: ~1 hour after sunrise, ~1 hour before sunset
        golden_morning = sunrise + pd.Timedelta(hours=1) if pd.notna(sunrise) else None
        golden_evening = sunset - pd.Timedelta(hours=1) if pd.notna(sunset) else None

        return {
            "sunrise": sunrise.isoformat() if pd.notna(sunrise) else None,
            "sunset": sunset.isoformat() if pd.notna(sunset) else None,
            "solar_noon": solar_noon.isoformat() if pd.notna(solar_noon) else None,
            "golden_hour_morning_end": golden_morning.isoformat() if golden_morning else None,
            "golden_hour_evening_start": golden_evening.isoformat() if golden_evening else None,
            "daylight_hours": round(
                (sunset - sunrise).total_seconds() / 3600, 1
            ) if pd.notna(sunrise) and pd.notna(sunset) else None,
        }
    except Exception as e:
        return {"error": str(e)}

