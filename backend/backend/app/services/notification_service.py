from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from app.models.alert import Alert


# ============================================================
# NOTIFICATION PROVIDER CONTRACT
# ============================================================
#
# Member 2:
#     API/service coordination
#
# Member 4:
#     Actual Firebase/FCM implementation
#
# Flow:
#
#     alert_service.py
#            |
#            v
#     notification_service.py
#            |
#            v
#     NotificationProvider
#            |
#            v
#     Member 4 Firebase / FCM
#
# ============================================================


class NotificationProvider(Protocol):
    """
    Contract for the actual notification delivery provider.
    """

    async def send(
        self,
        notification: Dict[str, Any],
    ) -> Any:
        """
        Deliver a notification.
        """
        ...

    async def cancel(
        self,
        notification_id: str,
    ) -> Any:
        """
        Cancel a previously created notification.
        """
        ...


# ============================================================
# PROVIDER INSTANCE
# ============================================================

_notification_provider: Optional[
    NotificationProvider
] = None


# ============================================================
# CONFIGURE PROVIDER
# ============================================================

def configure_notification_provider(
    provider: NotificationProvider,
) -> None:
    """
    Register the concrete notification provider.

    Member 4 can inject the Firebase/FCM implementation here.
    """

    global _notification_provider

    if provider is None:
        raise ValueError(
            "Notification provider cannot be None."
        )

    _notification_provider = provider


# ============================================================
# GET PROVIDER
# ============================================================

def get_notification_provider() -> Optional[
    NotificationProvider
]:
    """
    Return the configured notification provider.

    None is allowed because the backend can still create
    alerts when notification infrastructure is unavailable.
    """

    return _notification_provider


# ============================================================
# BUILD ALERT NOTIFICATION
# ============================================================

def build_alert_notification(
    alert: Alert,
) -> Dict[str, Any]:
    """
    Convert an Alert model into a provider-independent
    notification payload.
    """

    if alert is None:
        raise ValueError(
            "Alert cannot be None."
        )

    return {
        "notification_id": (
            f"alert_notification_{alert.id}"
        ),

        "type": "emergency_alert",

        "title": alert.title,

        "message": alert.message,

        "alert_id": alert.id,

        "severity": (
            alert.severity.value
        ),

        "audience": (
            alert.audience.value
        ),

        "data": {
            "alert_id": alert.id,
            "type": "emergency_alert",
            "severity": (
                alert.severity.value
            ),
        },
    }


# ============================================================
# SEND ALERT NOTIFICATION
# ============================================================

async def send_alert_notification(
    alert: Alert,
) -> Any:
    """
    Send an emergency alert notification.

    This function is intentionally provider-agnostic.

    The actual Firebase/FCM implementation is injected later.
    """

    if alert is None:
        raise ValueError(
            "Alert cannot be None."
        )

    notification = build_alert_notification(
        alert
    )

    provider = get_notification_provider()

    # --------------------------------------------------------
    # Notification infrastructure is not connected yet.
    # --------------------------------------------------------

    if provider is None:

        return {
            "success": False,
            "sent": False,
            "provider": None,
            "notification": notification,
            "message": (
                "Notification provider is not configured."
            ),
        }

    # --------------------------------------------------------
    # Send through configured provider.
    # --------------------------------------------------------

    result = await provider.send(
        notification
    )

    return result


# ============================================================
# CANCEL ALERT NOTIFICATION
# ============================================================

async def cancel_alert_notification(
    alert: Alert,
) -> Any:
    """
    Cancel/revoke an emergency alert notification.
    """

    if alert is None:
        raise ValueError(
            "Alert cannot be None."
        )

    notification_id = (
        f"alert_notification_{alert.id}"
    )

    provider = get_notification_provider()

    # --------------------------------------------------------
    # Provider unavailable.
    # --------------------------------------------------------

    if provider is None:

        return {
            "success": False,
            "cancelled": False,
            "provider": None,
            "notification_id": notification_id,
            "message": (
                "Notification provider is not configured."
            ),
        }

    # --------------------------------------------------------
    # Cancel through configured provider.
    # --------------------------------------------------------

    result = await provider.cancel(
        notification_id
    )

    return result


# ============================================================
# GENERIC NOTIFICATION
# ============================================================

async def send_notification(
    notification: Dict[str, Any],
) -> Any:
    """
    Send a generic notification.

    Useful later for:
        - SOS notifications
        - incident notifications
        - system notifications
        - shelter notifications
    """

    if not isinstance(
        notification,
        dict,
    ):

        raise ValueError(
            "Notification must be a dictionary."
        )

    if not notification:

        raise ValueError(
            "Notification cannot be empty."
        )

    provider = get_notification_provider()

    if provider is None:

        return {
            "success": False,
            "sent": False,
            "provider": None,
            "notification": notification,
            "message": (
                "Notification provider is not configured."
            ),
        }

    return await provider.send(
        notification
    )


# ============================================================
# NOTIFICATION AVAILABILITY
# ============================================================

def is_notification_provider_configured() -> bool:
    """
    Check whether a concrete notification provider
    has been connected.
    """

    return (
        _notification_provider
        is not None
    )


# ============================================================
# ALERT NOTIFICATION ID
# ============================================================

def get_alert_notification_id(
    alert_id: str,
) -> str:
    """
    Generate the stable notification identifier for an alert.
    """

    if not alert_id:
        raise ValueError(
            "Alert ID is required."
        )

    return (
        f"alert_notification_{alert_id}"
    )


# ============================================================
# PUBLIC NOTIFICATION DATA
# ============================================================

def notification_to_public_data(
    result: Any,
) -> Dict[str, Any]:
    """
    Convert a provider result into a JSON-safe response.

    This keeps provider-specific response objects from leaking
    directly through the API layer.
    """

    if result is None:

        return {
            "success": False,
            "result": None,
        }

    if isinstance(
        result,
        dict,
    ):

        return result

    return {
        "success": True,
        "result": result,
    }