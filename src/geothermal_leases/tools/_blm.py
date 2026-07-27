"""Shared constants and helpers for the BLM MLRS Geothermal Leases FeatureServer."""

from datetime import datetime, timezone

BASE_URL = (
    "https://gis.blm.gov/nlsdb/rest/services/HUB"
    "/BLM_Natl_MLRS_Geothermal_Leases/FeatureServer/0/query"
)


def ts_to_date(ms: int | None) -> str | None:
    """Convert ArcGIS epoch-milliseconds to an ISO date string."""
    if ms is None:
        return None
    # BLM uses very large values (year 2999+) to mean "no expiration"
    if ms > 32_503_593_600_000:
        return "No expiration"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def to_arcgis_timestamp(date_str: str) -> str:
    """Validate an ISO date string ('YYYY-MM-DD') and return an ArcGIS
    ``TIMESTAMP`` literal for use in a WHERE clause.

    Raises:
        ValueError: if ``date_str`` is not a valid 'YYYY-MM-DD' date.
    """
    # Raises ValueError on bad input; caller surfaces a clean tool error.
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    return f"TIMESTAMP '{parsed.strftime('%Y-%m-%d')} 00:00:00'"
