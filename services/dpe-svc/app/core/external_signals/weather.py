import os
from datetime import date

import httpx

WEATHER_API_BASE = os.getenv("WEATHER_API_BASE", "https://api.weather.gov")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

SEVERE_CONDITIONS = {
    "thunderstorms",
    "heavy rain",
    "snow",
    "blizzard",
    "ice",
    "hurricane",
    "tornado",
    "extreme cold",
    "extreme heat",
}


class WeatherSignalClient:
    def __init__(self, base_url: str = WEATHER_API_BASE, api_key: str = WEATHER_API_KEY):
        self.base_url = base_url
        self.api_key = api_key

    def get_capacity_adjustment_factor(
        self, work_center_location: str, forecast_date: date
    ) -> float:
        if not self.api_key or "placeholder" in self.api_key:
            return self._mock_factor(work_center_location, forecast_date)

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    f"{self.base_url}/points/{work_center_location}/forecast",
                    headers={"User-Agent": "ipe-dpe-svc/1.0"},
                )
                resp.raise_for_status()
                periods = resp.json().get("properties", {}).get("periods", [])
                for period in periods:
                    if forecast_date.strftime("%Y-%m-%d") in period.get("startTime", ""):
                        short_forecast = (period.get("shortForecast") or "").lower()
                        for cond in SEVERE_CONDITIONS:
                            if cond in short_forecast:
                                return 0.7
                        return 1.0
        except Exception:
            pass

        return 1.0

    @staticmethod
    def _mock_factor(work_center_location: str, forecast_date: date) -> float:
        location_hash = sum(ord(c) for c in work_center_location)
        day_of_year = forecast_date.timetuple().tm_yday
        combined = (location_hash + day_of_year) % 10
        if combined < 2:
            return 0.7
        if combined < 4:
            return 0.85
        return 1.0
