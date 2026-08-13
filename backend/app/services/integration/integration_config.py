import os


# =========================
# API Configuration
# =========================

API_BASE_URL = os.getenv("API_BASE_URL", "")

API_TIMEOUT = int(
    os.getenv("API_TIMEOUT", "10")
)


# =========================
# AI Configuration
# =========================

AI_API_URL = os.getenv("AI_API_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")


# =========================
# Map Configuration
# =========================

MAP_API_URL = os.getenv("MAP_API_URL", "")
MAP_API_KEY = os.getenv("MAP_API_KEY", "")


# =========================
# Database Configuration
# =========================

DATABASE_TYPE = os.getenv(
    "DATABASE_TYPE",
    "firebase"
)


# =========================
# Integration Settings
# =========================

INTEGRATION_ENABLED = (
    os.getenv("INTEGRATION_ENABLED", "true").lower()
    == "true"
)


def get_integration_config():
    """
    Return all integration configuration settings.
    """

    return {
        "api_base_url": API_BASE_URL,
        "api_timeout": API_TIMEOUT,
        "ai_api_url": AI_API_URL,
        "map_api_url": MAP_API_URL,
        "database_type": DATABASE_TYPE,
        "integration_enabled": INTEGRATION_ENABLED,
    }