from garminconnect import Garmin, GarminConnectConnectionError
from fastapi import HTTPException
from functools import lru_cache
from app.core.config import get_settings

@lru_cache()
def get_garmin_client() -> Garmin:
    """
    Returns a cached Garmin client instance.
    The cache is cleared when the application restarts.
    """
    settings = get_settings()
    try:
        client = Garmin(settings.GARMIN_EMAIL, settings.GARMIN_PASS)
        client.login()
        return client
    except GarminConnectConnectionError:
        raise HTTPException(status_code=503, detail="Failed to connect to Garmin Connect")
