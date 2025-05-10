from fastapi import FastAPI, HTTPException, Query
from garminconnect import Garmin, GarminConnectConnectionError
from dotenv import load_dotenv
import os
import datetime

app = FastAPI(title="Garmin Metrics API")

# Load environment variables from .env file
load_dotenv()
email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASS")

@app.get("/vo2max", summary="Retrieve yesterday's VO2Max data")
def get_vo2max():
    """
    Retrieves the VO2Max value for the previous day.
    Garmin typically computes this post-activity if matching some requirements.
    """
    client = connect_garmin()
    today = datetime.date.today()
    return client.get_max_metrics(today)

@app.get("/hrv", summary="Retrieve yesterday's HRV (heart rate variability)")
def get_hrv():
    """
    Retrieves the HRV data for the previous day.
    Garmin typically computes each 5 min while sleeping.
    """
    client = connect_garmin()
    today = datetime.date.today().isoformat()
    hrv_data = client.get_hrv_data(today)
    return format_hrv_readings(hrv_data)


@app.get("/respiratory_rate", summary="Retrieve respiratory rate data, optionally filtered by half-day")
def get_respiration(full: bool = Query(default=False, description="Set to true to return the full day")):
    """
    Retrieves respiratory rate data for today.
    Garmin takes readings roughly every 2 minutes.

    - If `full=false` (default): filters by time of day (00:00–12:00 or 12:00–23:59)
    - If `full=true`: returns all available data for the day
    """
    client = connect_garmin()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    respiratory_data = client.get_respiration_data(yesterday)

    measurements_raw = respiratory_data.get('respirationValuesArray', [])
    now = datetime.datetime.now()
    current_hour = now.hour

    if full:
        # No filtering, return all valid entries
        measurements = [
            {
                "datetime": datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                "value": value
            }
            for ts, value in measurements_raw if value > 0
        ]
    else:
        # Filter by time of day
        measurements = filter_by_half_day(measurements_raw, current_hour)

    return {
        "calendar_date": respiratory_data.get("calendarDate"),
        "measurements": measurements
    }

@app.get("/spo2", summary="Retrieve SpO2 (oxygen saturation) for yesterday")
def get_spo2():
    """
    Retrieves blood oxygen level (SpO2) hourly averages for the previous day.
    Garmin generally takes readings during sleep (depends on watch settings).
    """
    client = connect_garmin()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    spo2_data = client.get_spo2_data(yesterday)

    measurements = []
    for timestamp_ms, value in spo2_data.get('spO2HourlyAverages', []):
        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000)
        measurements.append({
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "value": value
        })

    return {
        "calendar_date": spo2_data.get("calendarDate"),
        "measurements": measurements
    }

def connect_garmin():
    """
    Authenticates and returns a Garmin API client instance.
    Raises HTTP 503 if authentication fails.
    """
    try:
        client = Garmin(email, password)
        client.login()
        return client
    except GarminConnectConnectionError:
        raise HTTPException(status_code=503, detail="Failed to connect to Garmin Connect")

def filter_by_half_day(measurements: list, current_hour: int) -> list:
    """
    Filters measurement entries into morning or afternoon buckets based on current time.
    - Before 12:00 → return 00:00–12:00 data
    - After 12:00 → return 12:00–23:59 data
    """
    filtered = []

    for entry in measurements:
        timestamp_ms, value = entry
        if value <= 0:
            continue

        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000)
        hour = dt.hour

        if current_hour < 12 and hour < 12:
            filtered.append({
                "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "value": value
            })
        elif current_hour >= 12 and hour >= 12:
            filtered.append({
                "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "value": value
            })

    return filtered

def format_hrv_readings(hrv_data: dict) -> dict:
    """
    Reformats raw HRV readings into a clean 'measurements' list.
    No aggregation, just conversion and formatting.
    """
    readings = hrv_data.get("hrvReadings", [])
    measurements = []

    for reading in readings:
        dt = datetime.datetime.strptime(reading["readingTimeLocal"], "%Y-%m-%dT%H:%M:%S.%f")
        measurements.append({
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "value": reading["hrvValue"]
        })

    return {
        "calendar_date": hrv_data.get("hrvSummary", {}).get("calendarDate", ""),
        "measurements": measurements
    }

