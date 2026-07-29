"""weather — Get current weather and forecast for any location worldwide.

Uses Open-Meteo API (free, no API key required).
Geocoding: converts city name → lat/lon.
Weather: fetches current conditions + multi-day forecast.
"""
from __future__ import annotations

import requests
from typing import Any


# WMO Weather Interpretation Codes → human-readable descriptions
WMO_CODES: dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    56: "Light Freezing Drizzle", 57: "Heavy Freezing Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    66: "Light Freezing Rain", 67: "Heavy Freezing Rain",
    71: "Slight Snowfall", 73: "Moderate Snowfall", 75: "Heavy Snowfall",
    77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
    85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail",
}

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def _geocode(location: str) -> dict[str, Any] | None:
    """Resolve a city/place name to latitude, longitude, and timezone."""
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results")
        if not results:
            return None
        r = results[0]
        return {
            "name": r.get("name", location),
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "timezone": r.get("timezone", "UTC"),
            "country": r.get("country", ""),
        }
    except requests.RequestException:
        return None


def get_weather(location: str, days: int = 1) -> dict[str, Any]:
    """Fetch current weather and multi-day forecast for a location.

    Args:
        location: City or place name (e.g. "Hanoi", "Hà Nội", "Paris").
        days: Number of forecast days (1–7). Default 1.

    Returns:
        Dict with current conditions, forecast, location info, and error status.
    """
    if not location or not location.strip():
        return {
            "error": "missing_location",
            "message": "Location is required. Please provide a city name.",
            "location": location,
            "current": None,
            "forecast": [],
        }

    days = max(1, min(int(days or 1), 7))

    # Step 1: Geocode
    geo = _geocode(location.strip())
    if not geo:
        return {
            "error": "location_not_found",
            "message": f"Could not find location: '{location}'. Try a different city name.",
            "location": location,
            "current": None,
            "forecast": [],
        }

    lat, lon = geo["latitude"], geo["longitude"]
    tz = geo["timezone"]

    # Step 2: Fetch weather
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "wind_speed_10m",
                "weather_code",
                "precipitation",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
            ],
            "forecast_days": days,
        }
        resp = requests.get(WEATHER_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Parse current
        curr = data.get("current", {})
        curr_units = data.get("current_units", {})
        wmo_curr = int(curr.get("weather_code", 0))
        current = {
            "temperature_c": curr.get("temperature_2m"),
            "feels_like_c": curr.get("apparent_temperature"),
            "humidity_pct": curr.get("relative_humidity_2m"),
            "wind_speed_kmh": curr.get("wind_speed_10m"),
            "precipitation_mm": curr.get("precipitation"),
            "weather_code": wmo_curr,
            "weather_description": WMO_CODES.get(wmo_curr, f"Code {wmo_curr}"),
        }

        # Parse daily forecast
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        forecast = []
        for i, date in enumerate(dates):
            wmo_day = int((daily.get("weather_code") or [])[i] or 0)
            forecast.append({
                "date": date,
                "temp_max_c": (daily.get("temperature_2m_max") or [])[i],
                "temp_min_c": (daily.get("temperature_2m_min") or [])[i],
                "precipitation_sum_mm": (daily.get("precipitation_sum") or [])[i],
                "weather_code": wmo_day,
                "weather_description": WMO_CODES.get(wmo_day, f"Code {wmo_day}"),
            })

        resolved_name = geo["name"]
        if geo.get("country"):
            resolved_name = f"{geo['name']}, {geo['country']}"

        return {
            "location": resolved_name,
            "latitude": lat,
            "longitude": lon,
            "timezone": tz,
            "current": current,
            "forecast": forecast,
            "error": None,
            "message": f"Weather data for {resolved_name} fetched successfully",
        }

    except requests.RequestException as exc:
        return {
            "error": "request_error",
            "message": str(exc),
            "location": location,
            "current": None,
            "forecast": [],
        }
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return {
            "error": "parse_error",
            "message": f"Failed to parse weather data: {exc}",
            "location": location,
            "current": None,
            "forecast": [],
        }
