import requests
from typing import Any, Optional


def get_request(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 10,
) -> Any:
    """
    Send a GET request to an external API.

    Args:
        url: API endpoint URL.
        params: Optional query parameters.
        headers: Optional HTTP headers.
        timeout: Request timeout in seconds.

    Returns:
        JSON response if available, otherwise text response.

    Raises:
        requests.RequestException: If the API request fails.
    """

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return response.text


def post_request(
    url: str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 10,
) -> Any:
    """
    Send a POST request to an external API.

    Args:
        url: API endpoint URL.
        data: Optional JSON payload.
        headers: Optional HTTP headers.
        timeout: Request timeout in seconds.

    Returns:
        JSON response if available, otherwise text response.

    Raises:
        requests.RequestException: If the API request fails.
    """

    response = requests.post(
        url,
        json=data,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return response.text