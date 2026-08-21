import asyncio
import importlib.util
import re
from pathlib import Path
from typing import Any

import requests

from app.services.maps.geocoding import geocode_address


PINCODE_PATTERN = re.compile(r"^\d{6}$")
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
EARTHQUAKE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USER_AGENT = "Smart-Campus-Emergency-Response-System"


def _load_existing_risk_engine():
    project_root = Path(__file__).resolve().parents[3]
    module_path = project_root / "ai" / "Ai_module.py"
    spec = importlib.util.spec_from_file_location("smart_campus_ai", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing AI risk module could not be loaded.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.predict_risk


def _resolve_pincode(pincode: str) -> dict[str, Any]:
    if not PINCODE_PATTERN.fullmatch(pincode):
        raise ValueError("Enter a valid six-digit Indian pincode.")

    result = geocode_address(f"{pincode}, India")
    if result is None:
        raise LookupError(f"Pincode {pincode} could not be located.")

    return result


def _fetch_live_weather(latitude: float, longitude: float) -> dict[str, Any]:
    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,precipitation,rain,showers,snowfall,"
                    "wind_speed_10m"
                ),
                "hourly": "precipitation_probability,precipitation,wind_speed_10m",
                "forecast_days": 1,
                "timezone": "auto",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return {
            "temperature_c": None,
            "precipitation_mm": None,
            "rain_mm": None,
            "showers_mm": None,
            "snowfall_cm": None,
            "wind_speed_kmh": None,
            "max_precipitation_probability": 0,
            "max_hourly_precipitation_mm": 0,
            "max_hourly_wind_speed_kmh": 0,
            "timezone": None,
            "provider_status": "unavailable",
        }
    current = payload.get("current")
    hourly = payload.get("hourly")
    if not isinstance(current, dict) or not isinstance(hourly, dict):
        raise RuntimeError("Live weather provider returned an incomplete response.")

    precipitation_probability = max(hourly.get("precipitation_probability") or [0])
    max_precipitation = max(hourly.get("precipitation") or [0])
    max_wind_speed = max(hourly.get("wind_speed_10m") or [0])

    return {
        "temperature_c": current.get("temperature_2m"),
        "precipitation_mm": current.get("precipitation"),
        "rain_mm": current.get("rain"),
        "showers_mm": current.get("showers"),
        "snowfall_cm": current.get("snowfall"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "max_precipitation_probability": precipitation_probability,
        "max_hourly_precipitation_mm": max_precipitation,
        "max_hourly_wind_speed_kmh": max_wind_speed,
        "timezone": payload.get("timezone"),
    }


def _calculate_weather_risks(weather: dict[str, Any]) -> dict[str, int]:
    """Convert live weather observations into transparent risk percentages."""

    precipitation_probability = float(
        weather["max_precipitation_probability"] or 0
    )
    precipitation_mm = float(
        weather["max_hourly_precipitation_mm"] or 0
    )
    wind_speed = float(weather["max_hourly_wind_speed_kmh"] or 0)

    flood_risk = min(
        100,
        round(max(precipitation_probability, precipitation_mm * 10)),
    )
    severe_weather_risk = min(
        100,
        round(max(precipitation_probability, wind_speed / 1.2)),
    )

    return {
        "flood_risk": flood_risk,
        "severe_weather_risk": severe_weather_risk,
    }


def _fetch_earthquake_risk(latitude: float, longitude: float) -> dict[str, Any]:
    """Use recent USGS events near the pincode to derive seismic activity."""

    try:
        response = requests.get(
            EARTHQUAKE_URL,
            params={
                "format": "geojson",
                "latitude": latitude,
                "longitude": longitude,
                "maxradiuskm": 500,
                "limit": 200,
                "orderby": "time",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        response.raise_for_status()
        features = response.json().get("features")
    except requests.RequestException:
        return {
            "earthquake_probability": 0,
            "recent_event_count": 0,
            "strongest_recent_magnitude": 0,
            "nearest_recent_events": [],
            "provider_status": "unavailable",
        }
    if not isinstance(features, list):
        raise RuntimeError("Earthquake provider returned an incomplete response.")

    recent_events = []
    for feature in features:
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2 or properties.get("mag") is None:
            continue
        recent_events.append({
            "magnitude": float(properties["mag"]),
            "place": properties.get("place"),
            "time": properties.get("time"),
            "longitude": coordinates[0],
            "latitude": coordinates[1],
        })

    strongest_magnitude = max(
        (event["magnitude"] for event in recent_events),
        default=0,
    )
    earthquake_probability = min(
        100,
        round(max(0, strongest_magnitude - 2) * 12),
    )

    return {
        "earthquake_probability": earthquake_probability,
        "recent_event_count": len(recent_events),
        "strongest_recent_magnitude": strongest_magnitude,
        "nearest_recent_events": recent_events[:5],
    }


def _predict_from_live_data(location: dict[str, Any], weather: dict[str, Any]) -> dict[str, Any]:
    predict_risk = _load_existing_risk_engine()
    risk_input = {
        "location_risk": location["display_name"],
        "flood": weather["max_hourly_precipitation_mm"] >= 2,
        "blocked_exit": weather["max_hourly_wind_speed_kmh"] >= 60,
    }
    result = predict_risk(risk_input)
    if not result.get("success"):
        raise RuntimeError(result.get("error", "Existing AI risk engine failed."))

    return result


async def predict_pincode_risk(pincode: str) -> dict[str, Any]:
    normalized_pincode = pincode.strip()
    location = await asyncio.to_thread(_resolve_pincode, normalized_pincode)
    weather = await asyncio.to_thread(
        _fetch_live_weather,
        location["latitude"],
        location["longitude"],
    )
    weather_risks = _calculate_weather_risks(weather)
    earthquake = await asyncio.to_thread(
        _fetch_earthquake_risk,
        location["latitude"],
        location["longitude"],
    )
    prediction = await asyncio.to_thread(
        _predict_from_live_data,
        location,
        weather,
    )

    return {
        "pincode": normalized_pincode,
        "location": location,
        "weather": weather,
        "risks": {
            **weather_risks,
            "earthquake_probability": earthquake["earthquake_probability"],
        },
        "earthquake": earthquake,
        "prediction": prediction,
    }