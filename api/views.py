from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    TemperatureStatsQuerySerializer,
    PrecipitationStatsQuerySerializer,
    SummaryQuerySerializer,
    TemperatureStatsResponseSerializer,
    PrecipitationStatsResponseSerializer,
    SummaryStatsResponseSerializer,
)
from services.exceptions import DatasetNotFound, InvalidDateRange
from services.stats import temperature_stats, precipitation_stats, summary_stats

# -----------------------------
# Swagger (query parameters)
# -----------------------------
CITY_PARAM = openapi.Parameter(
    name="city",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    required=True,
    description="City name (case-insensitive). Example: Madrid",
)

START_DATE_PARAM = openapi.Parameter(
    name="start_date",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE,
    required=True,
    description="Start date (YYYY-MM-DD).",
)

END_DATE_PARAM = openapi.Parameter(
    name="end_date",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_DATE,
    required=True,
    description="End date (YYYY-MM-DD).",
)

ABOVE_PARAM = openapi.Parameter(
    name="above",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_NUMBER,
    required=False,
    description="Temperature threshold (default: 30).",
)

BELOW_PARAM = openapi.Parameter(
    name="below",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_NUMBER,
    required=False,
    description="Temperature threshold (default: 0).",
)

ERROR_400 = openapi.Response(description="Validation error / invalid date range.")
ERROR_404 = openapi.Response(description="Dataset not found for the requested city/date range.")


class TemperatureStatsView(APIView):
    @swagger_auto_schema(
        operation_summary="Temperature statistics",
        operation_description=(
                "Returns aggregated temperature statistics for a given city and date range. "
                "Includes min/max, averages, and hours above/below thresholds."
        ),
        tags=["Weather"],
        manual_parameters=[CITY_PARAM, START_DATE_PARAM, END_DATE_PARAM, ABOVE_PARAM, BELOW_PARAM],
        responses={
            200: TemperatureStatsResponseSerializer,
            400: ERROR_400,
            404: ERROR_404,
        },
    )
    def get(self, request):
        in_ser = TemperatureStatsQuerySerializer(data=request.query_params)
        in_ser.is_valid(raise_exception=True)
        data = in_ser.validated_data

        try:
            result = temperature_stats(
                city_name=data["city"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                above=data["above"],
                below=data["below"],
            )
        except InvalidDateRange as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DatasetNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        out_ser = TemperatureStatsResponseSerializer(data=result)
        out_ser.is_valid(raise_exception=True)
        return Response(out_ser.data, status=status.HTTP_200_OK)


class PrecipitationStatsView(APIView):
    @swagger_auto_schema(
        operation_summary="Precipitation statistics",
        operation_description="Returns aggregated precipitation statistics for a given city and date range.",
        tags=["Weather"],
        manual_parameters=[CITY_PARAM, START_DATE_PARAM, END_DATE_PARAM],
        responses={
            200: PrecipitationStatsResponseSerializer,
            400: ERROR_400,
            404: ERROR_404,
        },
    )
    def get(self, request):
        in_ser = PrecipitationStatsQuerySerializer(data=request.query_params)
        in_ser.is_valid(raise_exception=True)
        data = in_ser.validated_data

        try:
            result = precipitation_stats(
                city_name=data["city"],
                start_date=data["start_date"],
                end_date=data["end_date"],
            )
        except InvalidDateRange as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DatasetNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        out_ser = PrecipitationStatsResponseSerializer(data=result)
        out_ser.is_valid(raise_exception=True)
        return Response(out_ser.data, status=status.HTTP_200_OK)


class SummaryStatsView(APIView):
    @swagger_auto_schema(
        operation_summary="Global summary",
        operation_description="Returns a global summary across all stored datasets.",
        tags=["Weather"],
        manual_parameters=[],
        responses={
            200: SummaryStatsResponseSerializer,
            400: ERROR_400,
        },
    )
    def get(self, request):
        in_ser = SummaryQuerySerializer(data=request.query_params)
        in_ser.is_valid(raise_exception=True)

        result = summary_stats()
        out_ser = SummaryStatsResponseSerializer(data=result)
        out_ser.is_valid(raise_exception=True)
        return Response(out_ser.data, status=status.HTTP_200_OK)
