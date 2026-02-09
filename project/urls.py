from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="OpenMeteoAPI",
        default_version="v1",
        description="Weather statistics API (Open-Meteo) – Django/DRF",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="swagger-json"),
    path('__debug__/', include('debug_toolbar.urls')),
]
