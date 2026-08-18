import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


def get_env(key: str, default=None):
    """
    Get an environment variable.
    Returns default value if the variable is not present.
    """
    return os.getenv(key, default)


def get_bool_env(key: str, default: bool = False) -> bool:
    """
    Read a boolean environment variable.
    """
    value = os.getenv(key)

    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int = 0) -> int:
    """
    Read an integer environment variable.
    """
    value = os.getenv(key)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default