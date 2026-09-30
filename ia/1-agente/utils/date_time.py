from datetime import datetime
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")


def get_current_timestamp() -> dict:
    """
    Returns the current date and time in America/Bogota as a structured dict.

    Returns:
        {
            "timezone": "America/Bogota",
            "datetime": "2026-09-30T23:55:00-05:00",
            "date": "2026-09-30",
            "time": "23:55:00",
            "day_of_week": "Wednesday",
            "utc_offset": "-05:00"
        }
    """
    now = datetime.now(tz=BOGOTA_TZ)
    offset = now.strftime("%z")          # e.g. "-0500"
    utc_offset = f"{offset[:3]}:{offset[3:]}"  # e.g. "-05:00"
    return {
        "timezone": "America/Bogota",
        "datetime": now.strftime(f"%Y-%m-%dT%H:%M:%S{utc_offset}"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "utc_offset": utc_offset,
    }
