from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from api.models import WeatherDataset
from services.queries import get_dataset_or_raise, _dataset_hours_to_df


# -----------------------
# Helpers
# -----------------------


def _fmt_dt(dt: pd.Timestamp) -> str:
    # PDF uses "YYYY-MM-DDTHH:00" without timezone (example: 2024-07-01T15:00) :contentReference[oaicite:5]{index=5}
    # We format in UTC consistently.
    return dt.strftime("%Y-%m-%dT%H:%M")


# -----------------------
# Temperature stats
# -----------------------

def temperature_stats(
        *,
        city_name: str,
        start_date: Any,
        end_date: Any,
        above: float = 30.0,
        below: float = 0.0,
) -> Dict[str, Any]:
    """
    Compute temperature statistics for a city and date range.

    Output matches the PDF structure:
    {
      "temperature": {
        "average": ...,
        "average_by_day": {...},
        "max": {"value": ..., "date_time": "..."},
        "min": {"value": ..., "date_time": "..."},
        "hours_above_threshold": ...,
        "hours_below_threshold": ...
      }
    }
    """
    dataset = get_dataset_or_raise(city_name=city_name, start_date=start_date, end_date=end_date)
    df = _dataset_hours_to_df(dataset)

    if df.empty:
        # Keep consistent schema but no data
        return {
            "temperature": {
                "average": None,
                "average_by_day": {},
                "max": None,
                "min": None,
                "hours_above_threshold": 0,
                "hours_below_threshold": 0,
            }
        }

    # global average
    avg = float(df["temperature"].mean())

    # average by day
    avg_by_day_series = df.groupby("date")["temperature"].mean()
    avg_by_day = {day: float(val) for day, val in avg_by_day_series.items()}

    # max/min with timestamp
    idx_max = df["temperature"].idxmax()
    idx_min = df["temperature"].idxmin()

    max_row = df.loc[idx_max]
    min_row = df.loc[idx_min]

    max_obj = {"value": float(max_row["temperature"]), "date_time": _fmt_dt(pd.Timestamp(max_row["timestamp"]))}
    min_obj = {"value": float(min_row["temperature"]), "date_time": _fmt_dt(pd.Timestamp(min_row["timestamp"]))}

    # hours above/below thresholds
    hours_above = int((df["temperature"] > above).sum())
    hours_below = int((df["temperature"] < below).sum())

    return {
        "temperature": {
            "average": avg,
            "average_by_day": avg_by_day,
            "max": max_obj,
            "min": min_obj,
            "hours_above_threshold": hours_above,
            "hours_below_threshold": hours_below,
        }
    }


# -----------------------
# Precipitation stats
# -----------------------

def precipitation_stats(
        *,
        city_name: str,
        start_date: Any,
        end_date: Any,
) -> Dict[str, Any]:
    """
    Output matches PDF structure:
    {
      "precipitation": {
        "total": ...,
        "total_by_day": {...},
        "days_with_precipitation": ...,
        "max": {"value": ..., "date": "..."},
        "average": ...
      }
    }
    """
    dataset = get_dataset_or_raise(city_name=city_name, start_date=start_date, end_date=end_date)
    df = _dataset_hours_to_df(dataset)

    if df.empty:
        return {
            "precipitation": {
                "total": 0.0,
                "total_by_day": {},
                "days_with_precipitation": 0,
                "max": None,
                "average": 0.0,
            }
        }

    total = float(df["precipitation"].sum())

    total_by_day_series = df.groupby("date")["precipitation"].sum()
    total_by_day = {day: float(val) for day, val in total_by_day_series.items()}

    # days with precipitation > 0mm (daily sum > 0)
    days_with_precip = int((total_by_day_series > 0).sum())

    # max precipitation day (by daily total)
    if len(total_by_day_series) > 0:
        day_max = total_by_day_series.idxmax()
        val_max = float(total_by_day_series.max())
        max_obj = {"value": val_max, "date": str(day_max)}
    else:
        max_obj = None

    # average precipitation in the range: interpret as average daily precipitation
    # (matches sample: average ~ total / number_of_days) :contentReference[oaicite:6]{index=6}
    num_days = max(1, len(total_by_day_series))
    avg = float(total / num_days)

    return {
        "precipitation": {
            "total": total,
            "total_by_day": total_by_day,
            "days_with_precipitation": days_with_precip,
            "max": max_obj,
            "average": avg,
        }
    }


# -----------------------
# Summary stats (for every dataset stored)
# -----------------------

def summary_stats() -> Dict[str, Any]:
    """
    Output matches PDF "global stats per city and range" format:
    {
      "Madrid": {
        "start_date": "...",
        "end_date": "...",
        "temperature_average": ...,
        "precipitation_total": ...,
        "days_with_precipitation": ...,
        "precipitation_max": {"date": "...", "value": ...},
        "temperature_max": {"date": "...", "value": ...},
        "temperature_min": {"date": "...", "value": ...}
      },
      ...
    }

    Note: If the same city has multiple datasets, keys would collide.
    For MVP, we use a composite key "City (start..end)" to avoid overwriting.
    If you prefer strictly "Madrid" as key, you must assume one dataset per city.
    """
    out: Dict[str, Any] = {}

    # Prefetch hours for fewer queries (still can be large, but ok for MVP scale)
    datasets = WeatherDataset.objects.select_related("city").all()

    for ds in datasets:
        df = _dataset_hours_to_df(ds)
        if df.empty:
            continue

        # daily totals for precipitation
        daily_precip = df.groupby("date")["precipitation"].sum()

        precip_total = float(df["precipitation"].sum())
        days_with_precip = int((daily_precip > 0).sum())

        # max precip day
        precip_max_date = daily_precip.idxmax()
        precip_max_val = float(daily_precip.max())
        precip_max = {"date": str(precip_max_date), "value": precip_max_val}

        # temperature average
        temp_avg = float(df["temperature"].mean())

        # temperature max/min by hour -> report day + value (PDF wants day in summary) :contentReference[oaicite:7]{index=7}
        idx_tmax = df["temperature"].idxmax()
        idx_tmin = df["temperature"].idxmin()
        tmax_row = df.loc[idx_tmax]
        tmin_row = df.loc[idx_tmin]

        tmax = {"date": str(tmax_row["date"]), "value": float(tmax_row["temperature"])}
        tmin = {"date": str(tmin_row["date"]), "value": float(tmin_row["temperature"])}

        key = f"{ds.city.name} ({ds.start_date}..{ds.end_date})"
        out[key] = {
            "start_date": str(ds.start_date),
            "end_date": str(ds.end_date),
            "temperature_average": temp_avg,
            "precipitation_total": precip_total,
            "days_with_precipitation": days_with_precip,
            "precipitation_max": precip_max,
            "temperature_max": tmax,
            "temperature_min": tmin,
        }

    return out
