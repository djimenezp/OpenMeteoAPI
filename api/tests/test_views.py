from datetime import datetime, timedelta, timezone as pytimezone

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import City, WeatherDataset, WeatherHour


class TestWeatherViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = timezone.localdate()

        # Keep a stable "past" range
        self.start_date = self.today - timedelta(days=10)
        self.end_date = self.today - timedelta(days=8)

        self.city = City.objects.create(
            name="Madrid",
            latitude=40.4168,
            longitude=-3.7038,
            country_code="ES",
            country="Spain",
            timezone="UTC"
        )

    # -----------------------
    # Temperature endpoint
    # -----------------------

    def test_temperature_missing_params_returns_400(self):
        resp = self.client.get("/api/weather/temperature/")
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        # city/start_date/end_date should be required
        self.assertIn("city", body)
        self.assertIn("start_date", body)
        self.assertIn("end_date", body)

    def test_temperature_end_date_not_past_returns_400(self):
        resp = self.client.get(
            "/api/weather/temperature/",
            {
                "city": "Madrid",
                "start_date": (self.today - timedelta(days=2)).isoformat(),
                "end_date": self.today.isoformat(),  # invalid: must be in the past
            },
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertIn("end_date", body)

    def test_temperature_dataset_not_found_returns_404(self):
        resp = self.client.get(
            "/api/weather/temperature/",
            {
                "city": "Madrid",
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertIn("detail", body)

    def test_temperature_ok_returns_200_and_shape(self):
        dataset = WeatherDataset.objects.create(
            city=self.city,
            start_date=self.start_date,
            end_date=self.end_date,
            source="open-meteo",
        )

        base_dt = datetime(
            self.start_date.year, self.start_date.month, self.start_date.day, 10, 0, 0,
            tzinfo=pytimezone.utc
        )
        WeatherHour.objects.bulk_create([
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=0), temperature=10.0, precipitation=0.0),
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=1), temperature=20.0, precipitation=1.0),
        ])

        resp = self.client.get(
            "/api/weather/temperature/",
            {
                "city": "Madrid",
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "above": 30,
                "below": 0,
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertIn("temperature", body)
        temp = body["temperature"]

        # basic contract keys
        self.assertIn("average", temp)
        self.assertIn("average_by_day", temp)
        self.assertIn("max", temp)
        self.assertIn("min", temp)
        self.assertIn("hours_above_threshold", temp)
        self.assertIn("hours_below_threshold", temp)

    # -----------------------
    # Precipitation endpoint
    # -----------------------

    def test_precipitation_missing_params_returns_400(self):
        resp = self.client.get("/api/weather/precipitation/")
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertIn("city", body)
        self.assertIn("start_date", body)
        self.assertIn("end_date", body)

    def test_precipitation_dataset_not_found_returns_404(self):
        resp = self.client.get(
            "/api/weather/precipitation/",
            {
                "city": "Madrid",
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertIn("detail", body)

    def test_precipitation_ok_returns_200_and_shape(self):
        dataset = WeatherDataset.objects.create(
            city=self.city,
            start_date=self.start_date,
            end_date=self.end_date,
            source="open-meteo",
        )

        base_dt = datetime(
            self.start_date.year, self.start_date.month, self.start_date.day, 10, 0, 0,
            tzinfo=pytimezone.utc
        )
        WeatherHour.objects.bulk_create([
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=0), temperature=10.0, precipitation=0.0),
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=1), temperature=20.0, precipitation=1.0),
        ])

        resp = self.client.get(
            "/api/weather/precipitation/",
            {
                "city": "Madrid",
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertIn("precipitation", body)
        prec = body["precipitation"]

        self.assertIn("total", prec)
        self.assertIn("total_by_day", prec)
        self.assertIn("days_with_precipitation", prec)
        self.assertIn("max", prec)
        self.assertIn("average", prec)

    # -----------------------
    # Summary endpoint
    # -----------------------

    def test_summary_ok_returns_200(self):
        resp = self.client.get("/api/weather/summary/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, dict)

    def test_summary_returns_data_when_dataset_exists(self):
        dataset = WeatherDataset.objects.create(
            city=self.city,
            start_date=self.start_date,
            end_date=self.end_date,
            source="open-meteo",
        )

        base_dt = datetime(
            self.start_date.year, self.start_date.month, self.start_date.day, 10, 0, 0,
            tzinfo=pytimezone.utc
        )
        WeatherHour.objects.bulk_create([
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=0), temperature=10.0, precipitation=0.0),
            WeatherHour(dataset=dataset, timestamp=base_dt + timedelta(hours=1), temperature=20.0, precipitation=1.0),
        ])

        resp = self.client.get("/api/weather/summary/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(len(body) >= 1)
