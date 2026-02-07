from django.urls import path

from api.views import TemperatureStatsView, PrecipitationStatsView, SummaryStatsView

urlpatterns = [
    path("weather/temperature/", TemperatureStatsView.as_view(), name="weather-temperature-stats"),
    path("weather/precipitation/", PrecipitationStatsView.as_view(), name="weather-precipitation-stats"),
    path("weather/summary/", SummaryStatsView.as_view(), name="weather-summary-stats"),
]