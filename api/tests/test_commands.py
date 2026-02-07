from datetime import datetime, timedelta, timezone as pytimezone
from unittest.mock import patch

import pandas as pd
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from api.models import City, WeatherDataset, WeatherHour


def _fake_hourly_df(start_date_iso: str) -> pd.DataFrame:
    """
    Build a tiny deterministic DataFrame matching the command expectations:
    columns: date, precipitation, temperature_2m
    """
    base_dt = datetime.fromisoformat(start_date_iso).replace(tzinfo=pytimezone.utc)
    rows = [
        {"date": base_dt + timedelta(hours=0), "precipitation": 0.0, "temperature_2m": 10.0},
        {"date": base_dt + timedelta(hours=1), "precipitation": 1.0, "temperature_2m": 20.0},
        {"date": base_dt + timedelta(hours=2), "precipitation": 2.0, "temperature_2m": 30.0},
    ]
    return pd.DataFrame(rows)


class TestLoadCityDataCommand(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.start_date = (today - timedelta(days=10)).isoformat()
        self.end_date = (today - timedelta(days=8)).isoformat()

    @patch("api.management.commands.loadcitydata.get_city_weather")
    def test_command_creates_city_dataset_and_hours(self, mock_get_city_weather):
        mock_get_city_weather.return_value = {
            "city": "Madrid",
            "country": "Spain",
            "country_iso": "ES",
            "latitude": 40.4168,
            "longitude": -3.7038,
            "timezone": "UTC",
            "hourly_data": _fake_hourly_df(self.start_date),
        }

        call_command("loadcitydata", "Madrid", self.start_date, self.end_date, "--countryISO", "ES", "--replace" )

        self.assertEqual(City.objects.count(), 1)
        city = City.objects.first()
        self.assertEqual(city.name, "Madrid")
        self.assertEqual(city.country_code, "ES")
        self.assertEqual(city.timezone, "UTC")

        self.assertEqual(WeatherDataset.objects.count(), 1)
        ds = WeatherDataset.objects.first()
        self.assertEqual(ds.city, city)
        self.assertEqual(ds.source, "open-meteo")

        self.assertEqual(WeatherHour.objects.count(), 3)

    @patch("api.management.commands.loadcitydata.get_city_weather")
    def test_command_replace_deletes_and_reinserts_hours(self, mock_get_city_weather):
        mock_get_city_weather.return_value = {
            "city": "Madrid",
            "country": "Spain",
            "country_iso": "ES",
            "latitude": 40.4168,
            "longitude": -3.7038,
            "timezone": "UTC",
            "hourly_data": _fake_hourly_df(self.start_date),
        }

        call_command("loadcitydata", "Madrid", self.start_date, self.end_date, "--countryISO", "ES", "--replace")
        self.assertEqual(WeatherHour.objects.count(), 3)

        # second run: different temp for first row, still 3 rows after replace
        df2 = _fake_hourly_df(self.start_date).copy()
        df2.loc[0, "temperature_2m"] = 99.0
        mock_get_city_weather.return_value["hourly_data"] = df2

        call_command("loadcitydata", "Madrid", self.start_date, self.end_date, "--countryISO", "ES", "--replace")
        self.assertEqual(WeatherHour.objects.count(), 3)

        first_hour = WeatherHour.objects.order_by("timestamp").first()
        self.assertAlmostEqual(first_hour.temperature, 99.0, places=6)

    @patch("api.management.commands.loadcitydata.get_city_weather")
    def test_command_without_replace_does_not_duplicate_existing_timestamps(self, mock_get_city_weather):
        mock_get_city_weather.return_value = {
            "city": "Madrid",
            "country": "Spain",
            "country_iso": "ES",
            "latitude": 40.4168,
            "longitude": -3.7038,
            "timezone": "UTC",
            "hourly_data": _fake_hourly_df(self.start_date),
        }

        # First run WITHOUT --replace
        call_command("loadcitydata", "Madrid", self.start_date, self.end_date, "--countryISO", "ES")
        self.assertEqual(WeatherHour.objects.count(), 3)

        # Second run WITHOUT --replace should skip duplicates
        call_command("loadcitydata", "Madrid", self.start_date, self.end_date, "--countryISO", "ES")
        self.assertEqual(WeatherHour.objects.count(), 3)
