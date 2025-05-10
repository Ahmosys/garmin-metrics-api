from datetime import datetime, date, timedelta

def format_datetime(dt: datetime) -> str:
    """Consistent datetime formatting across the application"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_yesterday() -> str:
    """Get yesterday's date in ISO format"""
    return (date.today() - timedelta(days=1)).isoformat()
