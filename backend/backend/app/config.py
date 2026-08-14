import os
from typing import List


# ============================================================
# ENVIRONMENT HELPER
# ============================================================

def get_env(
    key: str,
    default: str = "",
) -> str:
    """
    Read a value from the environment.

    Parameters
    ----------
    key:
        Name of the environment variable.

    default:
        Value returned when the variable is not available.

    Returns
    -------
    str
        Environment variable value.
    """

    value = os.getenv(key)

    if value is None:
        return default

    return value.strip()


# ============================================================
# BOOLEAN ENVIRONMENT HELPER
# ============================================================

def get_bool_env(
    key: str,
    default: bool = False,
) -> bool:
    """
    Convert an environment variable into a boolean.

    Accepted true values:
        true
        1
        yes
        on

    Accepted false values:
        false
        0
        no
        off
    """

    value = os.getenv(key)

    if value is None:
        return default

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


# ============================================================
# LIST ENVIRONMENT HELPER
# ============================================================

def get_list_env(
    key: str,
    default: str = "",
) -> List[str]:
    """
    Read a comma-separated environment variable.

    Example:

        ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

    becomes:

        [
            "http://localhost:5500",
            "http://127.0.0.1:5500"
        ]
    """

    value = get_env(key, default)

    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# APPLICATION SETTINGS
# ============================================================

class Settings:
    """
    Central configuration class for the backend.

    All application-level configuration is kept here instead
    of scattering environment-variable access throughout
    the project.

    Other modules can import:

        from app.config import settings

    and then use:

        settings.APP_NAME
        settings.DEBUG
        settings.ALLOWED_ORIGINS
    """

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    APP_NAME: str = get_env(
        "APP_NAME",
        "Smart Campus Emergency Response System",
    )

    APP_VERSION: str = get_env(
        "APP_VERSION",
        "1.0.0",
    )

    DEBUG: bool = get_bool_env(
        "DEBUG",
        True,
    )

    ENVIRONMENT: str = get_env(
        "ENVIRONMENT",
        "development",
    )

    # --------------------------------------------------------
    # SERVER
    # --------------------------------------------------------

    HOST: str = get_env(
        "HOST",
        "127.0.0.1",
    )

    PORT: int = int(
        get_env(
            "PORT",
            "8000",
        )
    )

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------
    #
    # These values are used by main.py.
    #
    # main.py:
    #
    #     allow_origins=settings.ALLOWED_ORIGINS
    #
    # --------------------------------------------------------

    ALLOWED_ORIGINS: List[str] = get_list_env(
        "ALLOWED_ORIGINS",
        "http://localhost:5500,"
        "http://127.0.0.1:5500,"
        "http://localhost:3000,"
        "http://127.0.0.1:3000",
    )

    # --------------------------------------------------------
    # JWT AUTHENTICATION
    # --------------------------------------------------------
    #
    # These settings will later be used by:
    #
    # app/utils/jwt_handler.py
    # app/dependencies.py
    # app/middleware/auth_middleware.py
    #
    # We keep them here so authentication configuration is
    # centralized.
    # --------------------------------------------------------

    JWT_SECRET_KEY: str = get_env(
        "JWT_SECRET_KEY",
        "change-this-secret-key-in-production",
    )

    JWT_ALGORITHM: str = get_env(
        "JWT_ALGORITHM",
        "HS256",
    )

    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        get_env(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
            "60",
        )
    )

    # --------------------------------------------------------
    # PASSWORD HASHING
    # --------------------------------------------------------

    PASSWORD_HASH_ALGORITHM: str = get_env(
        "PASSWORD_HASH_ALGORITHM",
        "bcrypt",
    )

    # --------------------------------------------------------
    # API SETTINGS
    # --------------------------------------------------------

    API_PREFIX: str = get_env(
        "API_PREFIX",
        "",
    )

    # --------------------------------------------------------
    # FILE UPLOAD SETTINGS
    # --------------------------------------------------------
    #
    # Image-analysis endpoint will receive uploaded images.
    # The actual AI image processing will remain outside the
    # backend route.
    # --------------------------------------------------------

    MAX_UPLOAD_SIZE_MB: int = int(
        get_env(
            "MAX_UPLOAD_SIZE_MB",
            "10",
        )
    )

    # --------------------------------------------------------
    # DATABASE / FIREBASE PLACEHOLDER CONFIGURATION
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # Firebase implementation belongs to Member 4's
    # services/database/ layer according to the project
    # structure.
    #
    # These environment variables are kept as configuration
    # values only. This file does NOT initialize Firebase.
    # --------------------------------------------------------

    FIREBASE_PROJECT_ID: str = get_env(
        "FIREBASE_PROJECT_ID",
    )

    FIREBASE_CLIENT_EMAIL: str = get_env(
        "FIREBASE_CLIENT_EMAIL",
    )

    FIREBASE_PRIVATE_KEY: str = get_env(
        "FIREBASE_PRIVATE_KEY",
    )

    # --------------------------------------------------------
    # AI / GEMINI CONFIGURATION
    # --------------------------------------------------------
    #
    # Actual Gemini/AI implementation belongs to Member 3.
    #
    # Backend can use the configuration value when the
    # integration layer is connected later.
    # --------------------------------------------------------

    GEMINI_API_KEY: str = get_env(
        "GEMINI_API_KEY",
    )

    GEMINI_MODEL: str = get_env(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )

    # --------------------------------------------------------
    # MAPS CONFIGURATION
    # --------------------------------------------------------
    #
    # Actual Maps implementation belongs to Member 4.
    #
    # Backend does not perform map calculations here.
    # --------------------------------------------------------

    MAPS_API_KEY: str = get_env(
        "MAPS_API_KEY",
    )

    # --------------------------------------------------------
    # NOTIFICATION CONFIGURATION
    # --------------------------------------------------------
    #
    # Notification service will be implemented separately.
    # These values allow future integration without changing
    # application code.
    # --------------------------------------------------------

    NOTIFICATION_ENABLED: bool = get_bool_env(
        "NOTIFICATION_ENABLED",
        True,
    )

    # --------------------------------------------------------
    # SECURITY SETTINGS
    # --------------------------------------------------------

    ENABLE_AUTH: bool = get_bool_env(
        "ENABLE_AUTH",
        True,
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    LOG_LEVEL: str = get_env(
        "LOG_LEVEL",
        "INFO",
    )

    # --------------------------------------------------------
    # CONFIGURATION VALIDATION
    # --------------------------------------------------------

    def validate(self) -> None:
        """
        Validate important configuration values.

        This method can be called during application startup
        when we finalize the backend configuration.
        """

        if not self.APP_NAME:
            raise ValueError(
                "APP_NAME cannot be empty."
            )

        if not self.JWT_ALGORITHM:
            raise ValueError(
                "JWT_ALGORITHM cannot be empty."
            )

        if self.PORT <= 0:
            raise ValueError(
                "PORT must be greater than zero."
            )

        if self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError(
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
            )

        if self.MAX_UPLOAD_SIZE_MB <= 0:
            raise ValueError(
                "MAX_UPLOAD_SIZE_MB must be greater than zero."
            )


# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================

settings = Settings()