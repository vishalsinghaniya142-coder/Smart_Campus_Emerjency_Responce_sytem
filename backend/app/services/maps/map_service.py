from app.services.maps.geocoding import geocode_address
from app.services.maps.location_service import (
    get_location,
    get_coordinates,
)
from app.services.maps.route_service import get_route
from app.services.maps.safe_route import get_safe_route


def search_location(address):
    """
    Search an address and return its coordinates.
    """

    return get_location(address)


def get_location_coordinates(address):
    """
    Get only latitude and longitude for an address.
    """

    return get_coordinates(address)


def find_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Find a normal route between two coordinates.
    """

    return get_route(
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude,
    )


def find_safe_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Find a safe route between two coordinates.
    """

    return get_safe_route(
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude,
    )


def geocode(address):
    """
    Direct access to geocoding service.
    """

    return geocode_address(address)