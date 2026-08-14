from typing import Any, Optional

from app.services.maps.map_service import search_location
from app.services.maps.route_service import get_route


def search_map_location(query: str) -> Optional[dict]:
    """
    Search for a location using the map service.
    """

    if not query:
        return None

    return search_location(query)


def get_map_route(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
) -> Optional[dict]:
    """
    Get a route between two geographic locations.
    """

    return get_route(
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude,
    )