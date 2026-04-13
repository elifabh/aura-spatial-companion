"""
Outdoor API — Profile-aware outdoor space recommendations.
Advises users on nearby parks/public spaces based on their profile and weather.
"""

from fastapi import APIRouter, HTTPException, Query
from backend.services.location import search_nearby
from backend.services.weather import get_current_weather
from backend.services.sun import get_sunrise_sunset
from backend.services.profile import get_user_profile

router = APIRouter()

@router.get("/nearby")
async def get_nearby_outdoor(
    lat: float, 
    lon: float, 
    user_id: str = "default",
    limit: int = 3
):
    """
    Get profile-tailored outdoor recommendations.
    Filters out bad weather directly (returns empty logic).
    """
    try:
        profile = get_user_profile(user_id)
        
        # 1. Weather check (fail-fast)
        weather = await get_current_weather(lat, lon)
        if weather.get("rain", 0) > 0.5:
            # It's heavily raining
            return []
            
        sun = get_sunrise_sunset(lat, lon)
        if hasattr(sun, 'get') and sun.get('daylight_hours', 0) == 0:
            pass # We could check if it's currently night here

        # Determine place types based on profile
        groups = []
        if profile:
            try:
                from backend.core.group_rules import detect_groups
                groups = detect_groups(profile)
            except Exception:
                pass
                
        search_query = "park"
        if "child" in groups:
            search_query = "playground"
        elif "elderly" in groups or "disability" in groups:
            search_query = "garden" # Generally flatter
            
        # 2. Fetch places
        places = await search_nearby(lat, lon, query=search_query)
        
        # Calculate rough distance in meters if not done by Nominatim
        import math
        def calc_dist(lat1, lon1, lat2, lon2):
            R = 6371e3
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2-lat1)
            dlambda = math.radians(lon2-lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        processed = []
        for p in places[:limit * 2]:  # fetch more, filter after
            p["distance_m"] = calc_dist(lat, lon, p["lat"], p["lon"])
            processed.append(p)
            
        # Sort by distance and filter out places farther than 3km
        processed.sort(key=lambda x: x["distance_m"])
        processed = [p for p in processed if p["distance_m"] <= 3000]
        return processed[:limit]
        
    except Exception as e:
        print(f"[Outdoor] Error: {e}")
        return []
