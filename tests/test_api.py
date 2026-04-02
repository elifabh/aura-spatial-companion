"""
API Tests — FastAPI endpoint testing.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test that the health endpoint responds correctly."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "aura"


def test_recommendation_categories():
    """Test that recommendation categories are returned."""
    response = client.get("/api/recommendations/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "safety" in categories
    assert "comfort" in categories


def test_chat_send_requires_message():
    """Test that chat endpoint validates input."""
    response = client.post("/api/chat/send", json={})
    assert response.status_code == 422  # Validation error


def test_weather_endpoint():
    """Test weather endpoint returns expected structure."""
    response = client.get("/api/weather/current")
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "source" in data


def test_sun_endpoint():
    """Test sun position endpoint."""
    response = client.get("/api/weather/sun")
    assert response.status_code == 200
    data = response.json()
    assert "altitude" in data
    assert "azimuth" in data
