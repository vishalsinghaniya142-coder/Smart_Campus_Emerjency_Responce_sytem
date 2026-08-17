import requests

from app.services.maps.map_config import (
    OSRM_URL,
    APP_NAME,
    REQUEST_TIMEOUT,
)


def get_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Get driving route between two coordinates.

    Returns:
        {
            "distance_km": float,
            "duration_minutes": float,
            "geometry": list
        }

    Returns None if route is not found.
    """

    coordinates = (
        f"{start_longitude},{start_latitude};"
        f"{end_longitude},{end_latitude}"
    )

    url = f"{OSRM_URL}/route/v1/driving/{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
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

    data = response.json()

    if data.get("code") != "Ok":
        return None

    routes = data.get("routes", [])

    if not routes:
        return None

    route = routes[0]

    return {
        "distance_km": round(
            route["distance"] / 1000,
            2,
        ),
        "duration_minutes": round(
            route["duration"] / 60,
            2,
        ),
        "geometry": route["geometry"]["coordinates"],
    }