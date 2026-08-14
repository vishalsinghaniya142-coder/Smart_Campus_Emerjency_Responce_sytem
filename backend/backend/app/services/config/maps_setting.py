from app.services.config.environment import get_env


MAPS_API_KEY = get_env("MAPS_API_KEY")
MAPS_BASE_URL = get_env(
    "MAPS_BASE_URL",
    "https://maps.googleapis.com/maps/api"
)


def get_maps_settings():
    """
    Return map service configuration.
    """
    return {
        "api_key": MAPS_API_KEY,
        "base_url": MAPS_BASE_URL,
    }