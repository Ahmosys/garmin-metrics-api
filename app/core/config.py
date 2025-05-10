from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    GARMIN_EMAIL: str = os.getenv("GARMIN_EMAIL", "")
    GARMIN_PASS: str = os.getenv("GARMIN_PASS", "")

def get_settings() -> Settings:
    return Settings()
