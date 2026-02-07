from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger('app')
from api.models import City, WeatherDataset, WeatherHour
from clients.open_meteo import get_city_weather


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("city", type=str, help="City name, e.g. Madrid")
        parser.add_argument("start_date", type=str, help="Start date (YYYY-MM-DD), must be in the past")
        parser.add_argument("end_date", type=str, help="End date (YYYY-MM-DD), must be in the past")
        parser.add_argument("-I", "--countryISO", type=str, default=None, help="Country ISO code (e.g. ES, FR)")
        parser.add_argument("-r", "--replace", action="store_true", help="If dataset exists, replace.")

    def handle(self, *args, **options):
        city_query: str = options["city"].strip()
        start_date_str: str = options["start_date"].strip()
        end_date_str: str = options["end_date"].strip()
        country: Optional[str] = options["countryISO"]
        replace: bool = bool(options["replace"])

        # Validate date imput
        self._validate_date_range(start_date_str, end_date_str)
        try:
            city_weather_info = get_city_weather(city_query, start_date_str, end_date_str, country)
        except Exception as e:
            raise CommandError(str(e))

        df = city_weather_info.pop("hourly_data")

        required_cols = {"date", "precipitation", "temperature_2m"}
        missing = required_cols - set(df.columns)
        if missing:
            raise CommandError(f"Unexpected dataframe columns. Missing: {sorted(missing)}")

        # Ensure datetime is aware (UTC). Your client uses utc=True already.
        # But we still coerce to be safe.
        df["date"] = df["date"].apply(self._ensure_aware_utc)
        data_json = json.loads(df.to_json(orient="records"))
        # 3) Persist into DB (atomic)
        with transaction.atomic():
            defaults = dict(
                country=city_weather_info["country"],
                latitude=city_weather_info["latitude"],
                longitude=city_weather_info["longitude"],
                data=data_json
            )
            city_obj, _ = City.objects.get_or_create(
                name=city_weather_info["city"],
                country_code=city_weather_info["country_iso"],
                defaults=defaults,
            )

            dataset, created = WeatherDataset.objects.get_or_create(
                city=city_obj,
                start_date=start_date_str,
                end_date=end_date_str,
                defaults={"source": "open-meteo"},
            )

            if not created and replace:
                WeatherHour.objects.filter(dataset=dataset).delete()

            # If not replacing and dataset exists, we prevent duplicates by skipping existing timestamps.
            existing_ts = set()
            if not created and not replace:
                existing_ts = set(
                    WeatherHour.objects.filter(dataset=dataset)
                    .values_list("timestamp", flat=True)
                )

            hours_to_create, skipped = [], []
            for row in df.itertuples(index=False):
                ts = row.date
                if existing_ts and ts in existing_ts:
                    skipped.append(ts)
                    continue

                hours_to_create.append(
                    WeatherHour(
                        dataset=dataset,
                        timestamp=ts,
                        precipitation=float(row.precipitation) if row.precipitation is not None else None,
                        temperature=float(row.temperature_2m) if row.temperature_2m is not None else None,
                    )
                )
            if hours_to_create:
                WeatherHour.objects.bulk_create(hours_to_create, batch_size=2000)


        self.print_stdout(f"Loaded {len(hours_to_create)} hourly rows for {city_obj} ")
        self.print_stdout(f"Skipped {len(skipped)} rows")
        self.print_stdout(f"[{start_date_str}..{end_date_str}]. ")
        self.print_stdout(f"Dataset {'created' if created else 'updated'}.")

    # -----------------------
    # Helpers
    # -----------------------

    @staticmethod
    def _parse_date(value: str, field_name: str) -> date:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise CommandError(f"{field_name} must be YYYY-MM-DD (got '{value}').")

    def _validate_date_range(self, start_date_str: str, end_date_str: str) -> None:
        start_d = self._parse_date(start_date_str, "start_date")
        end_d = self._parse_date(end_date_str, "end_date")
        if start_d > end_d:
            raise CommandError("start_date must be <= end_date.")

        today = timezone.localdate()
        # Requirement: always in the past (end date must be < today)
        if end_d >= today:
            raise CommandError(f"end_date must be in the past (today is {today.isoformat()}).")

    @staticmethod
    def _ensure_aware_utc(dt):
        if dt is None:
            return None
        if timezone.is_aware(dt):
            return dt
        return timezone.make_aware(dt, timezone=timezone.utc)

    def print_stdout(self, msg: str):
        self.stdout.write(
            self.style.SUCCESS(msg)
        )
