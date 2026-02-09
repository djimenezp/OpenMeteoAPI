from datetime import timedelta
from django.test import SimpleTestCase
from django.utils import timezone

from api.serializers import (
    TemperatureStatsQuerySerializer,
    PrecipitationStatsQuerySerializer,
    TemperatureStatsResponseSerializer,
    PrecipitationStatsResponseSerializer,
    SummaryStatsResponseSerializer,
)


class TestInputSerializers(SimpleTestCase):
    def test_temperature_query_defaults_thresholds(self):
        today = timezone.localdate()
        payload = {
            "city": "Madrid",
            "start_date": (today - timedelta(days=5)).isoformat(),
            "end_date": (today - timedelta(days=3)).isoformat(),
            # no above/below
        }
        s = TemperatureStatsQuerySerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["above"], 30.0)
        self.assertEqual(s.validated_data["below"], 0.0)

    def test_temperature_query_rejects_end_date_not_in_past(self):
        today = timezone.localdate()
        payload = {
            "city": "Madrid",
            "start_date": (today - timedelta(days=2)).isoformat(),
            "end_date": today.isoformat(),  # not allowed, must be in the past
        }
        s = TemperatureStatsQuerySerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_temperature_query_rejects_start_after_end(self):
        today = timezone.localdate()
        payload = {
            "city": "Madrid",
            "start_date": (today - timedelta(days=1)).isoformat(),
            "end_date": (today - timedelta(days=3)).isoformat(),
        }
        s = TemperatureStatsQuerySerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertTrue("non_field_errors" in s.errors or "start_date" in s.errors)

    def test_temperature_query_rejects_above_below_inverted(self):
        today = timezone.localdate()
        payload = {
            "city": "Madrid",
            "start_date": (today - timedelta(days=5)).isoformat(),
            "end_date": (today - timedelta(days=3)).isoformat(),
            "above": -5,
            "below": 10,
        }
        s = TemperatureStatsQuerySerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertTrue("non_field_errors" in s.errors or "above" in s.errors)

    def test_precipitation_query_valid(self):
        today = timezone.localdate()
        payload = {
            "city": "Madrid",
            "start_date": (today - timedelta(days=5)).isoformat(),
            "end_date": (today - timedelta(days=3)).isoformat(),
        }
        s = PrecipitationStatsQuerySerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)


class TestOutputSerializers(SimpleTestCase):
    def test_temperature_output_contract_valid(self):
        payload = {
            "temperature": {
                "average": 18.7,
                "average_by_day": {
                    "2024-07-01": 18.7,
                    "2024-07-02": 18.8,
                },
                "max": {"value": 33.2, "date_time": "2024-07-01T15:00"},
                "min": {"value": 7.1, "date_time": "2024-07-01T06:00"},
                "hours_above_threshold": 5,
                "hours_below_threshold": 2,
            }
        }
        s = TemperatureStatsResponseSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    def test_temperature_output_contract_rejects_missing_key(self):
        # missing "hours_below_threshold"
        payload = {
            "temperature": {
                "average": 18.7,
                "average_by_day": {"2024-07-01": 18.7},
                "max": {"value": 33.2, "date_time": "2024-07-01T15:00"},
                "min": {"value": 7.1, "date_time": "2024-07-01T06:00"},
                "hours_above_threshold": 5,
            }
        }
        s = TemperatureStatsResponseSerializer(data=payload)
        self.assertFalse(s.is_valid())
        self.assertIn("temperature", s.errors)
        self.assertIn("hours_below_threshold", s.errors['temperature'])

    def test_precipitation_output_contract_valid(self):
        payload = {
            "precipitation": {
                "total": 5.8,
                "total_by_day": {
                    "2024-07-01": 1.5,
                    "2024-07-02": 0.6,
                    "2024-07-03": 3.7,
                },
                "days_with_precipitation": 2,
                "max": {"value": 3.7, "date": "2024-07-03"},
                "average": 1.93,
            }
        }
        s = PrecipitationStatsResponseSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    def test_summary_output_contract_valid_dynamic_keys(self):
        payload = {
            "Madrid (2024-07-01..2024-07-03)": {
                "start_date": "2024-07-01",
                "end_date": "2024-07-03",
                "temperature_average": 18.7,
                "precipitation_total": 5.8,
                "days_with_precipitation": 2,
                "precipitation_max": {"date": "2024-07-03", "value": 3.7},
                "temperature_max": {"date": "2024-07-01", "value": 33.2},
                "temperature_min": {"date": "2024-07-02", "value": 7.1},
            }
        }
        s = SummaryStatsResponseSerializer(data=payload)
        self.assertTrue(s.is_valid(), s.errors)

    def test_summary_output_contract_rejects_invalid_item(self):
        # missing precipitation_max
        payload = {
            "Madrid (2024-07-01..2024-07-03)": {
                "start_date": "2024-07-01",
                "end_date": "2024-07-03",
                "temperature_average": 18.7,
                "precipitation_total": 5.8,
                "days_with_precipitation": 2,
                "temperature_max": {"date": "2024-07-01", "value": 33.2},
                "temperature_min": {"date": "2024-07-02", "value": 7.1},
            }
        }
        s = SummaryStatsResponseSerializer(data=payload)
        self.assertFalse(s.is_valid())
        # error should be under "data" or top-level depending on your implementation
        self.assertTrue(bool(s.errors))
        self.assertIn("data", s.errors)
        self.assertIn("Madrid (2024-07-01..2024-07-03)", s.errors['data'])
        self.assertIn("precipitation_max", s.errors['data']["Madrid (2024-07-01..2024-07-03)"])
