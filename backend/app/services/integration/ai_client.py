import os
import requests
from typing import Any, Optional


def get_ai_config() -> dict:
    """
    Get AI API configuration from environment variables.
    """

    return {
        "api_url": os.getenv("AI_API_URL"),
        "api_key": os.getenv("AI_API_KEY"),
    }


def call_ai(
    prompt: str,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> Any:
    """
    Send a prompt to the configured AI API.

    Args:
        prompt: User prompt for the AI.
        api_url: Optional AI API URL.
        api_key: Optional API key.
        timeout: Request timeout in seconds.

    Returns:
        AI API response.

    Raises:
        ValueError: If AI configuration is missing.
        requests.RequestException: If the API request fails.
    """

    config = get_ai_config()

    api_url = api_url or config["api_url"]
    api_key = api_key or config["api_key"]

    if not api_url:
        raise ValueError("AI_API_URL is not configured.")

    if not api_key:
        raise ValueError("AI_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
    }

    response = requests.post(
        api_url,
        json=payload,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return response.text