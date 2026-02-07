from datetime import datetime, timedelta, timezone as pytimezone

from django.test import TestCase
from django.utils import timezone

from api.models import City, WeatherDataset, WeatherHour
from api.serializers import (
    TemperatureStatsResponseSerializer,
    PrecipitationStatsResponseSerializer,
)

from services.stats import temperature_stats, precipitation_stats
from services.exceptions import DatasetNotFound


class TestServicesStats(TestCase):
    def setUp(self):
        self.city = City.objects.create(
            name="Madrid",
            latitude=40.4168,
            longitude=-3.7038,
            country_code="ES",
            country="Spain",
            timezone="UTC"
        )

        # Pick a deterministic past range
        today = timezone.localdate()
        self.start_date = today - timedelta(days=10)
        self.end_date = today - timedelta(days=8)

        self.dataset = WeatherDataset.objects.create(
            city=self.city,
            start_date=self.start_date,
            end_date=self.end_date,
            source="open-meteo",
            data={},
        )

        # Create 6 hourly points across 2 days (UTC)
        # Day1: 3 hours, Day2: 3 hours
        # Temperatures: [10, 20, 30] day1 avg=20
        #               [5, 15, 25]  day2 avg=15
        # Global avg = (10+20+30+5+15+25)/6 = 105/6 = 17.5
        # Max = 30 at day1 hour3, Min = 5 at day2 hour1
        # Precip: [0, 1, 2] day1 total=3
        #         [0, 0, 4] day2 total=4
        # Range precip total = 7
        # days_with_precip = 2 (both daily totals > 0)
        base_dt = datetime(
            self.start_date.year, self.start_date.month, self.start_date.day, 10, 0, 0,
            tzinfo=pytimezone.utc
        )
        points = [
            (base_dt + timedelta(hours=0), 10.0, 0.0),
            (base_dt + timedelta(hours=1), 20.0, 1.0),
            (base_dt + timedelta(hours=2), 30.0, 2.0),

            (base_dt + timedelta(days=1, hours=0), 5.0, 0.0),
            (base_dt + timedelta(days=1, hours=1), 15.0, 0.0),
            (base_dt + timedelta(days=1, hours=2), 25.0, 4.0),
        ]

        WeatherHour.objects.bulk_create([
            WeatherHour(
                dataset=self.dataset,
                timestamp=ts,
                temperature=temp,
                precipitation=prec,
            )
            for ts, temp, prec in points
        ])

    def test_temperature_stats_dataset_not_found(self):
        with self.assertRaises(DatasetNotFound):
            temperature_stats(
                city_name="Sevilla",
                start_date=self.start_date,
                end_date=self.end_date,
                above=30,
                below=0,
            )

    def test_temperature_stats_values_and_contract(self):
        result = temperature_stats(
            city_name="Madrid",
            start_date=self.start_date,
            end_date=self.end_date,
            above=18.0,   # threshold to count >18
            below=8.0,    # threshold to count <8
        )

        # Contract validation (output serializer)
        out = TemperatureStatsResponseSerializer(data=result)
        self.assertTrue(out.is_valid(), out.errors)

        temp = result["temperature"]
        self.assertAlmostEqual(temp["average"], 17.5, places=6)

        # average_by_day keys should be YYYY-MM-DD strings
        # day1 avg=20, day2 avg=15
        day1 = (self.start_date).isoformat()
        day2 = (self.start_date + timedelta(days=1)).isoformat()
        self.assertAlmostEqual(temp["average_by_day"][day1], 20.0, places=6)
        self.assertAlmostEqual(temp["average_by_day"][day2], 15.0, places=6)

        self.assertEqual(temp["max"]["value"], 30.0)
        self.assertTrue(temp["max"]["date_time"].startswith(day1))  # "YYYY-MM-DDT..."

        self.assertEqual(temp["min"]["value"], 5.0)
        self.assertTrue(temp["min"]["date_time"].startswith(day2))

        # > 18: temps are 20, 30, 25 => 3
        self.assertEqual(temp["hours_above_threshold"], 3)
        # < 8: temps are 5 => 1
        self.assertEqual(temp["hours_below_threshold"], 1)

    def test_precipitation_stats_values_and_contract(self):
        result = precipitation_stats(
            city_name="Madrid",
            start_date=self.start_date,
            end_date=self.end_date,
        )

        out = PrecipitationStatsResponseSerializer(data=result)
        self.assertTrue(out.is_valid(), out.errors)

        prec = result["precipitation"]
        self.assertAlmostEqual(prec["total"], 7.0, places=6)

        day1 = self.start_date.isoformat()
        day2 = (self.start_date + timedelta(days=1)).isoformat()
        self.assertAlmostEqual(prec["total_by_day"][day1], 3.0, places=6)
        self.assertAlmostEqual(prec["total_by_day"][day2], 4.0, places=6)

        self.assertEqual(prec["days_with_precipitation"], 2)

        self.assertEqual(prec["max"]["date"], day2)
        self.assertAlmostEqual(prec["max"]["value"], 4.0, places=6)

        # average daily = total / number_of_days = 7 / 2 = 3.5
        self.assertAlmostEqual(prec["average"], 3.5, places=6)
