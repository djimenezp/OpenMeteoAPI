from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
from django.utils import timezone

from api.models import WeatherDataset, City
from services.exceptions import InvalidDateRange, DatasetNotFound


def _parse_date(value: Any) -> date:
    """
    Accepts a date object or a YYYY-MM-DD string and returns a date.
    Keeps it permissive so the future view/serializer can pass either.
    """
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise InvalidDateRange(f"Invalid date value: {value!r}")


def _validate_past_range(start_d: date, end_d: date) -> None:
    if start_d > end_d:
        raise InvalidDateRange("start_date must be <= end_date")

    today = timezone.localdate()
    # Requirement: always in the past (end_date must be < today)
    if end_d >= today:
        raise InvalidDateRange(f"end_date must be in the past (today is {today.isoformat()})")


def get_dataset_or_raise(*, city_name: str, start_date: Any, end_date: Any) -> WeatherDataset:
    """
    Resolve the dataset for a city and a date range.
    The dataset must exist (it should have been created by loadcitydata command).
    """
    start_d = _parse_date(start_date)
    end_d = _parse_date(end_date)
    _validate_past_range(start_d, end_d)

    # Basic city lookup: name match.
    # If you later want to support country_code disambiguation, add it here.
    city = City.objects.filter(name__iexact=city_name).first()
    if not city:
        raise DatasetNotFound(f"City '{city_name}' not found in DB. Load it first.")

    dataset = WeatherDataset.objects.filter(city=city, start_date=start_d, end_date=end_d).first()
    if not dataset:
        raise DatasetNotFound(
            f"No dataset found for city='{city.name}' start_date='{start_d}' end_date='{end_d}'. "
            "Run: python manage.py loadcitydata <city> <start> <end> --replace"
        )

    return dataset


def _dataset_hours_to_df(dataset: WeatherDataset) -> pd.DataFrame:
    """
    Load all WeatherHour rows for a dataset into a pandas DataFrame.

    Columns:
      - timestamp (datetime, tz-aware)
      - date (YYYY-MM-DD string)
      - temperature
      - precipitation
    """
    # Fetch only the fields we need, ordered by timestamp asc for stable min/max picking
    qs = dataset.hours.all().only("timestamp", "temperature", "precipitation").order_by("timestamp")
    rows = list(qs.values("timestamp", "temperature", "precipitation"))

    if not rows:
        return pd.DataFrame(columns=["timestamp", "date", "temperature", "precipitation"])

    df = pd.DataFrame(rows)
    # Ensure timestamp is datetime, and keep timezone awareness
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Day key: in the simplest version we use UTC day.
    # If you want local day by city timezone later, convert here.
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")

    return df
