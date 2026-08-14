from app.services.maps.geocoding import geocode_address


def get_location(address):
    """
    Get coordinates for an address.

    Returns:
        {
            "address": str,
            "latitude": float,
            "longitude": float,
            "display_name": str
        }

    Returns None if the location is not found.
    """

    result = geocode_address(address)

    if result is None:
        return None

    return {
        "address": address,
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "display_name": result["display_name"],
    }


def get_coordinates(address):
    """
    Return only latitude and longitude.
    """

    location = get_location(address)

    if location is None:
        return None

    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }
    
    