from datetime import datetime, timezone


def parse_datetime(value: str | None) -> datetime | None:
    """
    Parse an ISO8601 timestamp from the Humanitix API.

    Returns None if the value is missing or invalid.
    """
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def ordinal(n: int) -> str:
    """
    Convert an integer to its ordinal representation.

    Examples:
        1 -> 1st
        2 -> 2nd
        3 -> 3rd
        4 -> 4th
        11 -> 11th
        21 -> 21st
    """
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(n % 10, "th")

    return f"{n}{suffix}"


def wheel_title(now: datetime | None = None) -> str:
    """
    Generate the title for today's prize wheel.
    """
    if now is None:
        now = datetime.now()

    return (
        f"Wheel of Prizes - "
        f"{ordinal(now.day)} "
        f"{now.strftime('%B %Y')}"
    )


def wheel_description(now: datetime | None = None) -> str:
    """
    Generate the default wheel description.
    """
    if now is None:
        now = datetime.now()

    return f"Created at {now.strftime('%Y-%m-%d %H:%M:%S')}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
