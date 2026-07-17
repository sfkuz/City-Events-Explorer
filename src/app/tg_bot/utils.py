from datetime import datetime, timedelta
import calendar

def resolve_dates(date_value: str | None, custom_from: str | None = None, custom_to: str | None = None) -> tuple[datetime | None, datetime | None]:
    if not date_value:
        return None, None

    now = datetime.now()

    if date_value == 'this_weekend':
        days_ahead = 4 - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        start = now - timedelta(days=days_ahead)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=2, hours=23, minutes=59, seconds=59, microseconds=59)
        return start, end

    elif date_value == "next_weekend":
        days_ahead = 4 - now.weekday() + 7
        start = now + timedelta(days=days_ahead)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=2, hours=23, minutes=59, seconds=59)
        return start, end

    elif date_value == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
        return start, end

    elif date_value == "own" and custom_from and custom_to:
        return datetime.fromisoformat(custom_from), datetime.fromisoformat(custom_to)

    return None, None