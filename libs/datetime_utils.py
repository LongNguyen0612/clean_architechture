from datetime import datetime, timezone


def get_now() -> datetime:
    """
    Returns the current UTC datetime with tzinfo removed.
    
    This standardizes timezone handling across the application by:
    1. Getting the current time in UTC
    2. Removing timezone info to work with naive datetime objects
    
    Returns:
        datetime: Current UTC time as a naive datetime object
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) 