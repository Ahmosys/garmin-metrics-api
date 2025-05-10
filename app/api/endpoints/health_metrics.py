from fastapi import APIRouter, Depends, Query
from garminconnect import Garmin
from app.models.metrics import MetricsResponse
from app.services.garmin import get_garmin_client
from app.utils.datetime_utils import get_yesterday
from app.utils.metrics_formatters import (
    format_hrv_readings,
    format_spo2_readings,
    format_respiratory_readings
)
from datetime import datetime, date

router = APIRouter()

@router.get("/vo2max", summary="Retrieve yesterday's VO2Max data")
def get_vo2max(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves the VO2Max value for the previous day.
    Garmin typically computes this post-activity if matching some requirements.
    """
    return client.get_max_metrics(date.today())

@router.get("/hrv", summary="Retrieve yesterday's HRV (heart rate variability)", response_model=MetricsResponse)
def get_hrv(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves the HRV data for the previous day.
    Garmin typically computes each 5 min while sleeping.
    """
    hrv_data = client.get_hrv_data(get_yesterday())
    return format_hrv_readings(hrv_data)

@router.get("/spo2", summary="Retrieve SpO2 (oxygen saturation) for yesterday", response_model=MetricsResponse)
def get_spo2(client: Garmin = Depends(get_garmin_client)):
    """
    Retrieves blood oxygen level (SpO2) hourly averages for the previous day.
    Garmin generally takes readings during sleep (depends on watch settings).
    """
    spo2_data = client.get_spo2_data(get_yesterday())
    return format_spo2_readings(spo2_data)

@router.get("/respiratory_rate", summary="Retrieve respiratory rate data, optionally filtered by half-day", response_model=MetricsResponse)
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
    return format_respiratory_readings(respiratory_data, datetime.now().hour, full)
