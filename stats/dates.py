import math
from datetime import datetime


def ymd(date) -> str | None:
    if date is None:
        return None
    return date.strftime("%Y-%m-%d")


def days_since(date, now=None) -> int:
    now = now or datetime.now()
    return (now - date).days


def js_round(value: float) -> int:
    """Round-half-up, matching JS Math.round for the non-negative values used here."""
    return math.floor(value + 0.5)


def round1(value: float) -> float:
    return js_round(value * 10) / 10
