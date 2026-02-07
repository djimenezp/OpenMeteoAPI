from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from api.serializers import (
    TemperatureStatsQuerySerializer,
    PrecipitationStatsQuerySerializer,
    SummaryQuerySerializer,
    TemperatureStatsResponseSerializer,
    PrecipitationStatsResponseSerializer,
    SummaryStatsResponseSerializer,
)

from services.stats import temperature_stats, precipitation_stats, summary_stats
from services.exceptions import DatasetNotFound, InvalidDateRange


class TemperatureStatsView(APIView):
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
    def get(self, request):
        in_ser = SummaryQuerySerializer(data=request.query_params)
        in_ser.is_valid(raise_exception=True)

        result = summary_stats()
        out_ser = SummaryStatsResponseSerializer(data=result)
        out_ser.is_valid(raise_exception=True)
        return Response(out_ser.data, status=status.HTTP_200_OK)
