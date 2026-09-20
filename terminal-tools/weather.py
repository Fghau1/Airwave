#!/usr/bin/env python3
"""Show current conditions and a five-day forecast using Open-Meteo."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
HEADERS = {"User-Agent": "AirwaveTerminalTools/1.0 (terminal weather)"}
CODES = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Freezing fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain",
    67: "Heavy freezing rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Light showers", 81: "Showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Heavy snow showers", 95: "Thunderstorm",
    96: "Thunderstorm, hail", 99: "Thunderstorm, heavy hail",
}


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def saved_city():
    path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "airwave-tools" / "city"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def save_city(city):
    path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "airwave-tools" / "city"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(city.strip() + "\n", encoding="utf-8")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--set-city":
        city = " ".join(args[1:]).strip() or input("Your city (e.g. Lisbon, Portugal): ").strip()
        if not city:
            print("Please enter a city.", file=sys.stderr)
            return 2
        try:
            lookup = get_json(GEOCODING + "?" + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"}))
            results = lookup.get("results", [])
            if not results:
                print(f"Could not find {city!r}.", file=sys.stderr)
                return 1
            place = results[0]
            label = ", ".join(p for p in (place["name"], place.get("admin1"), place.get("country")) if p)
            save_city(label)
            print(f"Default weather location saved: {label}")
            return 0
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"Location lookup failed: {error}", file=sys.stderr)
            return 1
    city = " ".join(args).strip() or saved_city()
    if not city:
        city = input("City (you can save a default with --set-city CITY): ").strip()
    if not city:
        print("Please provide a city name.", file=sys.stderr)
        return 2
    try:
        lookup = get_json(GEOCODING + "?" + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"}))
        results = lookup.get("results", [])
        if not results:
            print(f"Could not find {city!r}.", file=sys.stderr)
            return 1
        place = results[0]
        params = urllib.parse.urlencode({
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto", "forecast_days": 5,
        })
        data = get_json(FORECAST + "?" + params)
        current = data["current"]
        unit = data["current_units"]
        label = ", ".join(p for p in (place["name"], place.get("admin1"), place.get("country")) if p)
        print(f"\nWeather for {label}")
        print(f"As of {current['time'].replace('T', ' ')} {data.get('timezone_abbreviation', '')}")
        code = CODES.get(current.get("weather_code"), "Unknown conditions")
        print(f"\n  {code}  ·  {current['temperature_2m']}{unit.get('temperature_2m', '°C')} (feels like {current['apparent_temperature']}{unit.get('apparent_temperature', '°C')})")
        print(f"  Humidity {current['relative_humidity_2m']}%  ·  Wind {current['wind_speed_10m']} {unit.get('wind_speed_10m', 'km/h')}")
        print(f"  Rain {current['rain']} {unit.get('rain', 'mm')}  ·  Precipitation {current['precipitation']} {unit.get('precipitation', 'mm')}")
        daily, du = data["daily"], data["daily_units"]
        print("\n  FIVE-DAY FORECAST")
        for i, day in enumerate(daily["time"]):
            condition = CODES.get(daily["weather_code"][i], "Unknown")
            chance = daily["precipitation_probability_max"][i]
            print(f"  {day}  {condition:<22} {daily['temperature_2m_min'][i]:g}° / {daily['temperature_2m_max'][i]:g}° {du.get('temperature_2m_min', 'C')}   rain chance {chance}%")
        print("\nData: Open-Meteo")
        return 0
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"Weather request failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
