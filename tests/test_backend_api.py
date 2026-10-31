import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Arc trip < 60 ms" in data["safety_target"]

@pytest.mark.asyncio
async def test_appliance_classes_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/appliances/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert data[0]["name"] == "Resistive Heater / Geyser"

@pytest.mark.asyncio
async def test_telemetry_ingestion():
    payload = {
        "mac_address": "AA:BB:CC:DD:EE:01",
        "v_rms": 230.5,
        "i_rms": 4.5,
        "active_power_p": 1037.2,
        "reactive_power_q": 45.0,
        "power_factor": 0.999,
        "frequency": 50.0,
        "detected_class_index": 0,
        "confidence": 0.98,
        "harmonics": [4.45, 0.02, 0.05, 0.01, 0.02, 0.01, 0.01]
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/telemetry/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mac_address"] == "AA:BB:CC:DD:EE:01"
    assert data["active_power_p"] == 1037.2

@pytest.mark.asyncio
async def test_arc_alert_reporting():
    alert_payload = {
        "mac_address": "AA:BB:CC:DD:EE:01",
        "di_dt_peak": 26.8,
        "spectral_entropy": 0.91,
        "consecutive_cycles": 3,
        "trip_latency_ms": 57.6,
        "relay_tripped": True,
        "benign_suppressed": False,
        "notes": "Series arcing detected during bench test"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/alerts/", json=alert_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["relay_tripped"] is True
    assert data["trip_latency_ms"] < 60.0

