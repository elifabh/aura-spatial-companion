"""
Location Service — OpenStreetMap Nominatim integration.
Provides geographic context for spatial recommendations.
Free API, no key required. Respects usage policy.
"""

import httpx
from backend.config import OPENSTREETMAP_NOMINATIM_URL


async def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse geocode coordinates to get location context.
    Returns address details and local area information.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OPENSTREETMAP_NOMINATIM_URL}/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                },
                headers={
                    "User-Agent": "Aura-Spatial-Companion/0.1",
                },
            )
            response.raise_for_status()
            data = response.json()

            address = data.get("address", {})
            return {
                "display_name": data.get("display_name", ""),
                "county": address.get("county", ""),
                "city": address.get("city", address.get("town", "")),
                "country": address.get("country", ""),
                "postcode": address.get("postcode", ""),
            }
    except Exception:
        return {
            "display_name": "Location unavailable",
            "county": "",
            "city": "",
            "country": "",
            "postcode": "",
        }


async def search_nearby(lat: float, lon: float, query: str = "park") -> list[dict]:
    """
    Search for nearby amenities using Nominatim.
    Useful for recommending outdoor activities.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{OPENSTREETMAP_NOMINATIM_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "viewbox": f"{lon-0.05},{lat+0.05},{lon+0.05},{lat-0.05}",
                    "bounded": 1,
                },
                headers={
                    "User-Agent": "Aura-Spatial-Companion/0.1",
                },
            )
            response.raise_for_status()
            results = response.json()

            return [
                {
                    "name": r.get("display_name", "").split(",")[0],
                    "lat": float(r.get("lat", 0)),
                    "lon": float(r.get("lon", 0)),
                    "type": r.get("type", ""),
                }
                for r in results
            ]
    except Exception:
        return []
