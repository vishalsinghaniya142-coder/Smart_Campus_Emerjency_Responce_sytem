from app.services.maps.route_service import get_route


def get_safe_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Get a route and return basic safety information.

    For now, the route is considered safe by default.

    Later this function can check:
        - active incidents
        - blocked roads
        - emergency zones
        - dangerous areas
    """

    route = get_route(
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
    )

    if route is None:
        return None

    return {
        "safe": True,
        "distance_km": route["distance_km"],
        "duration_minutes": route["duration_minutes"],
        "geometry": route["geometry"],
    }