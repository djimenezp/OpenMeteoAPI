import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup session with caching and retries
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
session = retry(cache_session, retries=5, backoff_factor=0.2)


def archive(latitude: float, longitude: float, start_date: str, end_date: str) -> pd.DataFrame:
    url = "https://archive-api.open-meteo.com/v1/archive"
    if not latitude or not longitude:
        raise ValueError("Latitude and longitude are required.")
    if not start_date or not end_date:
        raise ValueError("Start and end date are required.")
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["precipitation", "temperature_2m"],
    }
    responses = openmeteo_requests.Client(session=session).weather_api(url, params=params)
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_precipitation = hourly.Variables(0).ValuesAsNumpy()
    hourly_temperature_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["temperature_2m"] = hourly_temperature_2m

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print("\nHourly data\n", hourly_dataframe)
    return hourly_dataframe


def geocode(name, countryCode: str = None, language: str = 'EN', count: int = 10) -> dict:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": name,
        "language": language,
        "count": count
    }
    if countryCode:
        params["countryCode"] = countryCode
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        response = response.json()
        return response["results"][0]
    except Exception:
        raise ValueError(f"City '{name}' not found for country code '{countryCode}'.")


def get_city_weather(city_name: str, start_date: str, end_date: str, country_iso:str=None) -> dict:
    city = geocode(city_name,country_iso)
    city_name = city.get("name") or city_name
    city_country = city.get("country") or ""
    city_country_iso = city.get("country_code") or ""
    latitude = city.get("latitude")
    longitude = city.get("longitude")
    timezone = city.get("timezone")
    if latitude is None or longitude is None:
        raise ValueError("Geocoding response missing latitude/longitude.")
    df = archive(city['latitude'], city['longitude'], start_date, end_date)
    if df is None or df.empty:
        raise ValueError("No hourly data found for the given city and range.")
    weather_info = {
        "city": city_name,
        "country": city_country,
        "country_iso": city_country_iso,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "hourly_data": df
    }
    return weather_info
