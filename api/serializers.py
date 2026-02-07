from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers


# -----------------------
# Input serializers (query params)
# -----------------------

class _BaseCityRangeQuerySerializer(serializers.Serializer):
    city = serializers.CharField(trim_whitespace=True, max_length=255)
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        start = attrs["start_date"]
        end = attrs["end_date"]

        if start > end:
            raise serializers.ValidationError("start_date must be <= end_date.")

        today = timezone.localdate()
        # Requirement: always in the past
        if end >= today:
            raise serializers.ValidationError(
                {"end_date": f"end_date must be in the past (today is {today.isoformat()})."}
            )

        return attrs


class TemperatureStatsQuerySerializer(_BaseCityRangeQuerySerializer):
    above = serializers.FloatField(required=False, default=30.0)
    below = serializers.FloatField(required=False, default=0.0)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        above = attrs["above"]
        below = attrs["below"]
        if above < below:
            raise serializers.ValidationError("above must be >= below.")

        return attrs


class PrecipitationStatsQuerySerializer(_BaseCityRangeQuerySerializer):
    pass


class SummaryQuerySerializer(serializers.Serializer):
    # No query params for now
    pass


# -----------------------
# Output serializers (response contracts)
# -----------------------

class TemperatureExtremaSerializer(serializers.Serializer):
    value = serializers.FloatField()
    date_time = serializers.CharField()  # "YYYY-MM-DDTHH:MM"


class TemperatureStatsInnerSerializer(serializers.Serializer):
    average = serializers.FloatField(allow_null=True)
    average_by_day = serializers.DictField(child=serializers.FloatField(), required=True)

    # max/min can be None if no data
    max = TemperatureExtremaSerializer(allow_null=True, required=False)
    min = TemperatureExtremaSerializer(allow_null=True, required=False)

    hours_above_threshold = serializers.IntegerField()
    hours_below_threshold = serializers.IntegerField()


class TemperatureStatsResponseSerializer(serializers.Serializer):
    temperature = TemperatureStatsInnerSerializer()


class PrecipitationMaxSerializer(serializers.Serializer):
    value = serializers.FloatField()
    date = serializers.CharField()  # "YYYY-MM-DD"


class PrecipitationStatsInnerSerializer(serializers.Serializer):
    total = serializers.FloatField()
    total_by_day = serializers.DictField(child=serializers.FloatField(), required=True)
    days_with_precipitation = serializers.IntegerField()

    max = PrecipitationMaxSerializer(allow_null=True, required=False)
    average = serializers.FloatField()


class PrecipitationStatsResponseSerializer(serializers.Serializer):
    precipitation = PrecipitationStatsInnerSerializer()


class SummaryPrecipitationMaxSerializer(serializers.Serializer):
    date = serializers.CharField()
    value = serializers.FloatField()


class SummaryTemperatureExtremeSerializer(serializers.Serializer):
    date = serializers.CharField()
    value = serializers.FloatField()


class SummaryStatsItemSerializer(serializers.Serializer):
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    temperature_average = serializers.FloatField()
    precipitation_total = serializers.FloatField()
    days_with_precipitation = serializers.IntegerField()
    precipitation_max = SummaryPrecipitationMaxSerializer()
    temperature_max = SummaryTemperatureExtremeSerializer()
    temperature_min = SummaryTemperatureExtremeSerializer()


class SummaryStatsResponseSerializer(serializers.Serializer):
    """
    Summary is a dict keyed by city or "City (start..end)".
    We validate values using SummaryStatsItemSerializer.
    """
    # DictField validates values, but not keys (fine for this use case)
    data = serializers.DictField(child=SummaryStatsItemSerializer())

    def to_representation(self, instance):
        # allow passing dict directly as "instance" and expose it as top-level dict
        return instance

    def to_internal_value(self, data):
        # validate dict-of-items under the hood, but keep top-level shape
        validated = super().to_internal_value({"data": data})
        return validated["data"]
