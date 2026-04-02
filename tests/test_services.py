"""
Service Tests — Weather, Sun, Profile, Location.
"""

import pytest


def test_sun_position_returns_dict():
    """Test pvlib sun position calculation."""
    from backend.services.sun import get_sun_position
    result = get_sun_position(53.3498, -6.2603)
    assert isinstance(result, dict)
    assert "altitude" in result
    assert "light_quality" in result


def test_profile_crud():
    """Test profile create/read/update cycle."""
    from backend.services.profile import get_user_profile, update_user_profile
    from backend.db.sqlite import init_db

    init_db()

    # Create
    profile = update_user_profile("test_user", {"interests": ["reading"]})
    assert profile["interests"] == ["reading"]

    # Read
    fetched = get_user_profile("test_user")
    assert fetched is not None
    assert fetched["interests"] == ["reading"]

    # Update
    updated = update_user_profile("test_user", {"space_type": "apartment"})
    assert updated["space_type"] == "apartment"
    assert updated["interests"] == ["reading"]  # preserved
