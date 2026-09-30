from datetime import datetime
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")


def get_current_timestamp() -> str:
    """
    Gets the current date and time in the format 'yyyy-MM-dd HH:mm:ss'.
    If a date is provided, combine the given date with the current time and include the day of the week.
    """
    date_time = datetime.now(tz=BOGOTA_TZ)
    current_day = date_time.strftime("%A")
    current_date = date_time.strftime("%Y-%m-%d %H:%M:%S")

    return f"{current_date} - Day of the week: {current_day}"
