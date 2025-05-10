from datetime import datetime
from app.models.metrics import MetricsResponse
from app.utils.datetime_utils import format_datetime

def format_hrv_readings(hrv_data: dict) -> MetricsResponse:
    """
    Reformats HRV readings into a clean 'measurements' list.
    """
    measurements = [
        {
            "datetime": format_datetime(datetime.strptime(reading["readingTimeLocal"], "%Y-%m-%dT%H:%M:%S.%f")),
            "value": reading["hrvValue"]
        }
        for reading in hrv_data.get("hrvReadings", [])
    ]

    return MetricsResponse(
        calendar_date=hrv_data.get("hrvSummary", {}).get("calendarDate", ""),
        measurements=measurements
    )

def format_spo2_readings(spo2_data: dict) -> MetricsResponse:
    """
    Reformats SpO2 readings into a clean 'measurements' list.
    """
    measurements = [
        {
            "datetime": format_datetime(datetime.fromtimestamp(timestamp_ms / 1000)),
            "value": value
        }
        for timestamp_ms, value in spo2_data.get('spO2HourlyAverages', [])
    ]

    return MetricsResponse(
        calendar_date=spo2_data.get("calendarDate"),
        measurements=measurements
    )

def format_respiratory_readings(respiratory_data: dict, current_hour: int, full: bool = False) -> MetricsResponse:
    """
    Reformats respiratory rate readings into a clean 'measurements' list.
    Optionally filters by time of day.
    """
    measurements_raw = respiratory_data.get('respirationValuesArray', [])

    if full:
        measurements = [
            {
                "datetime": format_datetime(datetime.fromtimestamp(ts / 1000)),
                "value": value
            }
            for ts, value in measurements_raw if value > 0
        ]
    else:
        measurements = filter_by_half_day(measurements_raw, current_hour)

    return MetricsResponse(
        calendar_date=respiratory_data.get("calendarDate"),
        measurements=measurements
    )

def filter_by_half_day(measurements: list, current_hour: int) -> list:
    """
    Filters measurement entries into morning or afternoon buckets based on current time.
    - Before 12:00 → return 00:00–12:00 data
    - After 12:00 → return 12:00–23:59 data
    """
    return [
        {
            "datetime": format_datetime(datetime.fromtimestamp(ts / 1000)),
            "value": value
        }
        for ts, value in measurements
        if value > 0 and (
            (current_hour < 12 and datetime.fromtimestamp(ts / 1000).hour < 12) or
            (current_hour >= 12 and datetime.fromtimestamp(ts / 1000).hour >= 12)
        )
    ]
