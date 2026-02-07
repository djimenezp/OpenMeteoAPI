from __future__ import annotations


class StatsError(Exception):
    """Base error for stats services."""


class DatasetNotFound(StatsError):
    """Raised when the city + date range dataset does not exist in DB."""


class InvalidDateRange(StatsError):
    """Raised when date params are invalid (e.g., end_date not in the past)."""
