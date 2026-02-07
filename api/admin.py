from django.contrib import admin
from .models import City, WeatherDataset, WeatherHour


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country_code", "country", "timezone", "latitude", "longitude")
    search_fields = ("name", "country", "country_code")
    list_filter = ("country_code", "timezone")
    ordering = ("name", "country_code")


@admin.register(WeatherDataset)
class WeatherDatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "start_date", "end_date", "source", "created_at", "hours_count")
    search_fields = ("city__name", "city__country", "city__country_code")
    list_filter = ("city__country_code", "source", "start_date", "end_date")
    ordering = ("-created_at",)
    readonly_fields = ("data",)  # JSON can be big

    def hours_count(self, obj):
        return obj.hours.count()
    hours_count.short_description = "hours"


@admin.register(WeatherHour)
class WeatherHourAdmin(admin.ModelAdmin):
    list_display = ("id", "dataset", "timestamp", "temperature", "precipitation")
    search_fields = ("dataset__city__name", "dataset__city__country_code")
    list_filter = ("dataset__city__country_code", "dataset__city__name")
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"
