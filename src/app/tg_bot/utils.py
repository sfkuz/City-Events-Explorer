from datetime import datetime, timedelta
import calendar
from zoneinfo import ZoneInfo

def resolve_dates(date_value: str | None, custom_from: str | None = None, custom_to: str | None = None) -> tuple[datetime | None, datetime | None]:
    if not date_value:
        return None, None

    tz = ZoneInfo("Europe/Warsaw")
    now = datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_value == 'this_weekend':
        weekday = now.weekday()
        if weekday >= 5:
            start = today_start
            days_to_sunday = 6 - weekday
            end = today_start + timedelta(days=days_to_sunday, hours=23, minutes=59, seconds=59)
        else:
            days_to_friday = 4 - weekday
            start = today_start + timedelta(days=days_to_friday)
            end = start + timedelta(days=2, hours=23, minutes=59, seconds=59)
        return start, end

    elif date_value == "next_weekend":
        weekday = now.weekday()
        days_to_next_friday = 4 - weekday +7
        start = today_start + timedelta(days=days_to_next_friday)
        end = start + timedelta(days=2, hours=23, minutes=59, seconds=59)
        return start, end

    elif date_value == "this_month":
        start = today_start
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
        return start, end

    elif date_value == "own" and custom_from and custom_to:
        return datetime.fromisoformat(custom_from), datetime.fromisoformat(custom_to)

    return None, None