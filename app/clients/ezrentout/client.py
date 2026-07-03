import httpx
from app.config import settings


def create_ezrentout_client() -> httpx.Client:
    """Return an HTTP client configured for the EZRentOut API.

    Creates an `httpx.Client` with the EZRentOut base URL,
    authentication headers, and default request timeout.
    """
    return httpx.Client(
        base_url=settings.ez_rentout_base_url,
        timeout=20.0,
        headers={
            "Authorization": f"Bearer {settings.ez_rentout_token}",
            "Accept": "application/json",
            },
        )
