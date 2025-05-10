from fastapi import FastAPI, HTTPException, Query, Depends
from garminconnect import Garmin, GarminConnectConnectionError
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import os
from functools import lru_cache

# Models
class Measurement(BaseModel):
    datetime: str
    value: float

class MetricsResponse(BaseModel):
    calendar_date: str
    measurements: List[Measurement]

# Configuration
class Settings:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv("GARMIN_EMAIL")
        self.password = os.getenv("GARMIN_PASS")
        if not self.email or not self.password:
            raise ValueError("GARMIN_EMAIL and GARMIN_PASS must be set in .env file")

settings = Settings()
app = FastAPI(title="Garmin Metrics API")

# Dependencies
@lru_cache()
def get_garmin_client() -> Garmin:
    """
    Returns a cached Garmin client instance.
    The cache is cleared when the application restarts.
    """
    try:
        client = Garmin(settings.email, settings.password)
        client.login()
        return client
    except GarminConnectConnectionError:
        raise HTTPException(status_code=503, detail="Failed to connect to Garmin Connect")

# Helper functions
def format_datetime(dt: datetime) -> str:
    """Consistent datetime formatting across the application"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_yesterday() -> str:
    """Get yesterday's date in ISO format"""
    return (date.today() - datetime.timedelta(days=1)).isoformat()

# Routes
@app.get("/vo2max", summary="Retrieve yesterday's VO2Max data", response_model=dict)
def get_vo2max(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves the VO2Max value for the previous day.
    Garmin typically computes this post-activity if matching some requirements.
    """
    return client.get_max_metrics(date.today())

@app.get("/hrv", summary="Retrieve yesterday's HRV (heart rate variability)", response_model=MetricsResponse)
def get_hrv(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves the HRV data for the previous day.
    Garmin typically computes each 5 min while sleeping.
    """
    hrv_data = client.get_hrv_data(get_yesterday())
    return format_hrv_readings(hrv_data)

@app.get("/respiratory_rate", summary="Retrieve respiratory rate data, optionally filtered by half-day", response_model=MetricsResponse)
def get_respiration(
    full: bool = Query(default=False, description="Set to true to return the full day"),
    client: Garmin = Depends(get_garmin_client)
):
    """
    Retrieves respiratory rate data for today.
    Garmin takes readings roughly every 2 minutes.

    - If `full=false` (default): filters by time of day (00:00–12:00 or 12:00–23:59)
    - If `full=true`: returns all available data for the day
    """
    respiratory_data = client.get_respiration_data(get_yesterday())
    measurements_raw = respiratory_data.get('respirationValuesArray', [])
    current_hour = datetime.now().hour

    if full:
        measurements = [
            Measurement(
                datetime=format_datetime(datetime.fromtimestamp(ts / 1000)),
                value=value
            )
            for ts, value in measurements_raw if value > 0
        ]
    else:
        measurements = filter_by_half_day(measurements_raw, current_hour)

    return MetricsResponse(
        calendar_date=respiratory_data.get("calendarDate"),
        measurements=measurements
    )

@app.get("/spo2", summary="Retrieve SpO2 (oxygen saturation) for yesterday", response_model=MetricsResponse)
def get_spo2(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves blood oxygen level (SpO2) hourly averages for the previous day.
    Garmin generally takes readings during sleep (depends on watch settings).
    """
    spo2_data = client.get_spo2_data(get_yesterday())

    measurements = [
        Measurement(
            datetime=format_datetime(datetime.fromtimestamp(timestamp_ms / 1000)),
            value=value
        )
        for timestamp_ms, value in spo2_data.get('spO2HourlyAverages', [])
    ]

    return MetricsResponse(
        calendar_date=spo2_data.get("calendarDate"),
        measurements=measurements
    )

def filter_by_half_day(measurements: List[tuple], current_hour: int) -> List[Measurement]:
    """
    Filters measurement entries into morning or afternoon buckets based on current time.
    - Before 12:00 → return 00:00–12:00 data
    - After 12:00 → return 12:00–23:59 data
    """
    return [
        Measurement(
            datetime=format_datetime(datetime.fromtimestamp(ts / 1000)),
            value=value
        )
        for ts, value in measurements
        if value > 0 and (
            (current_hour < 12 and datetime.fromtimestamp(ts / 1000).hour < 12) or
            (current_hour >= 12 and datetime.fromtimestamp(ts / 1000).hour >= 12)
        )
    ]

def format_hrv_readings(hrv_data: dict) -> MetricsResponse:
    """
    Reformats raw HRV readings into a clean 'measurements' list.
    No aggregation, just conversion and formatting.
    """
    measurements = [
        Measurement(
            datetime=format_datetime(datetime.strptime(reading["readingTimeLocal"], "%Y-%m-%dT%H:%M:%S.%f")),
            value=reading["hrvValue"]
        )
        for reading in hrv_data.get("hrvReadings", [])
    ]

    return MetricsResponse(
        calendar_date=hrv_data.get("hrvSummary", {}).get("calendarDate", ""),
        measurements=measurements
    )

