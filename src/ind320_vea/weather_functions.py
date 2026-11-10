from pathlib import Path
from datetime import date

import geopandas as gpd
import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
import streamlit as st
from retry_requests import retry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEATHER_API_URL = "https://archive-api.open-meteo.com/v1/archive"

VASS_REGIONS = {
    1: ("RS", "R\u00D8"),
    2: ("RV",),
    3: ("RM", "RN"),
}
PRECIPITATION_REGIONS = ("RV", "RS", "R\u00D8", "RM", "RN")


def weather_regions_for_area(selected_area):
    area_type, area_number = selected_area
    area_number = int(area_number)

    if area_type == "EL":
        return (f"NO{area_number}",)
    if area_type == "VASS":
        return VASS_REGIONS[area_number]
    if area_type == "NO":
        return PRECIPITATION_REGIONS
    raise ValueError(f"Unknown reservoir area type: {area_type}")


@st.cache_data(show_spinner=False)
def get_weather_coordinates():
    coordinates = {}

    electricity_path = PROJECT_ROOT / "Notebooks" / "data" / "Budområder" / "Budområder.shp"
    electricity_areas = gpd.read_file(electricity_path)
    electricity_points = electricity_areas.geometry.sample_points(
        size=1000, random_state=42
    ).to_crs(epsg=4326)

    for index, multipoint in electricity_points.items():
        region = electricity_areas.loc[index, "budomr"].replace(" ", "")
        coordinates[region] = [
            (point.x, point.y) for point in multipoint.geoms
        ]

    precipitation_path = (
        PROJECT_ROOT / "Notebooks" / "data" / "NVE_Region" / "NVE_Region.shp"
    )
    precipitation_areas = gpd.read_file(precipitation_path, encoding="UTF-8")
    precipitation_points = precipitation_areas.geometry.sample_points(
        size=1000, random_state=42
    ).to_crs(epsg=4326)

    for index, multipoint in precipitation_points.items():
        region = precipitation_areas.loc[index, "REGION"]
        coordinates[region] = [
            (point.x, point.y) for point in multipoint.geoms
        ]

    for region in ("NO1", "NO2", "NO3", "NO4", "NO5", *PRECIPITATION_REGIONS):
        if region not in coordinates or len(coordinates[region]) != 1000:
            raise ValueError(f"Expected 1000 sampled locations for {region}.")

    return coordinates


def validate_weather_dates(start_date, end_date):
    start_date = pd.Timestamp(start_date).date()
    end_date = pd.Timestamp(end_date).date()

    if start_date < date(1940, 1, 1):
        raise ValueError("ERA5 data is available from 1940-01-01.")
    if end_date > date.today():
        raise ValueError("The end date cannot be in the future.")
    if end_date < start_date:
        raise ValueError("The end date must be on or after the start date.")
    if (end_date - start_date).days > 365:
        raise ValueError("Choose a period of no more than one year.")
    return start_date, end_date


def weather_data_session_key(selected_area, start_date, end_date):
    area_type, area_number = selected_area
    start_date, end_date = validate_weather_dates(start_date, end_date)
    return (
        area_type,
        int(area_number),
        start_date.isoformat(),
        end_date.isoformat(),
    )


@st.cache_resource
def get_openmeteo_client():
    cache_session = requests_cache.CachedSession(
        backend="memory",
        expire_after=-1,
    )
    retry_session = retry(cache_session, retries=5, backoff_factor=0.5)
    return openmeteo_requests.Client(session=retry_session)


def average_weather_responses(responses):
    if not responses:
        raise ValueError("The Open-Meteo API returned no responses.")

    time_index = None
    temperature_sum = None
    temperature_count = None
    precipitation_sum = None
    precipitation_count = None

    for response in responses:
        hourly = response.Hourly()
        if hourly is None:
            raise ValueError("An Open-Meteo response has no hourly data.")

        temperature = np.asarray(
            hourly.Variables(0).ValuesAsNumpy(), dtype=float
        )
        precipitation = np.asarray(
            hourly.Variables(1).ValuesAsNumpy(), dtype=float
        )
        response_time = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            periods=len(temperature),
            freq=pd.Timedelta(seconds=hourly.Interval()),
        )
        if len(temperature) != len(precipitation):
            raise ValueError("Temperature and precipitation lengths do not match.")

        if time_index is None:
            time_index = response_time
            temperature_sum = np.zeros(len(temperature))
            temperature_count = np.zeros(len(temperature))
            precipitation_sum = np.zeros(len(precipitation))
            precipitation_count = np.zeros(len(precipitation))
        elif not time_index.equals(response_time):
            raise ValueError("Open-Meteo returned different time ranges for locations.")

        valid_temperature = np.isfinite(temperature)
        temperature_sum[valid_temperature] += temperature[valid_temperature]
        temperature_count[valid_temperature] += 1

        valid_precipitation = np.isfinite(precipitation)
        precipitation_sum[valid_precipitation] += precipitation[valid_precipitation]
        precipitation_count[valid_precipitation] += 1

    if (temperature_count == 0).any() or (precipitation_count == 0).any():
        raise ValueError("Some hours have no valid weather measurements.")

    return pd.DataFrame({
        "time": time_index,
        "temperature_2m": temperature_sum / temperature_count,
        "precipitation": precipitation_sum / precipitation_count,
    })


def download_weather_data(
    selected_area, start_date, end_date, progress_callback=None
):
    start_date, end_date = validate_weather_dates(start_date, end_date)

    regions = weather_regions_for_area(selected_area)
    coordinates_by_region = get_weather_coordinates()
    coordinates = [
        point
        for region in regions
        for point in coordinates_by_region[region]
    ]

    batch_size = 25
    batch_count = (len(coordinates) + batch_size - 1) // batch_size
    batch_averages = []
    client = get_openmeteo_client()

    for batch_number, batch_start in enumerate(
        range(0, len(coordinates), batch_size), start=1
    ):
        batch = coordinates[batch_start:batch_start + batch_size]
        longitudes, latitudes = zip(*batch)
        params = {
            "latitude": list(latitudes),
            "longitude": list(longitudes),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": ["temperature_2m", "precipitation"],
            "models": "era5",
            "timezone": "UTC",
        }
        responses = client.weather_api(WEATHER_API_URL, params=params, timeout=120)
        if len(responses) != len(batch):
            raise ValueError(
                f"Expected {len(batch)} API responses, received {len(responses)}."
            )
        batch_averages.append(average_weather_responses(responses))

        if progress_callback is not None:
            progress_callback(batch_number, batch_count)

    weighted_batches = []
    for batch_average, batch_start in zip(
        batch_averages,
        range(0, len(coordinates), batch_size),
    ):
        batch_size_actual = min(batch_size, len(coordinates) - batch_start)
        weighted_average = batch_average.set_index("time")
        weighted_batches.append(weighted_average * batch_size_actual)
    weather_data = (
        pd.concat(weighted_batches)
        .groupby("time")
        .sum()
        .div(len(coordinates))
        .reset_index()
    )
    expected_hours = ((end_date - start_date).days + 1) * 24
    if len(weather_data) != expected_hours:
        raise ValueError(
            f"Expected {expected_hours} hourly values from {start_date} to {end_date}, "
            f"received {len(weather_data)}."
        )

    return weather_data
