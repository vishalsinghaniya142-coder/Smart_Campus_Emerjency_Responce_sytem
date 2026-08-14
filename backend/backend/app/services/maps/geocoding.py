import requests

from app.services.maps.map_config import (
    NOMINATIM_URL,
    APP_NAME,
    REQUEST_TIMEOUT,
)


def geocode_address(address):
    """
    Convert an address into latitude and longitude.

    Returns:
        {
            "latitude": float,
            "longitude": float,
            "display_name": str
        }

        Returns None if the address cannot be found.
    """

    url = f"{NOMINATIM_URL}/search"

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": APP_NAME,
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    return {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "display_name": result["display_name"],
    }