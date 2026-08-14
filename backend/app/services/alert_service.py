from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.models.alert import (
    Alert,
    AlertAudience,
    AlertCreate,
    AlertSeverity,
    AlertStatus,
    AlertType,
    build_alert,
    get_alert_update_data,
    is_alert_active,
)

from app.schemas.alert_schema import (
    AlertCreateRequest,
    AlertFilterRequest,
    AlertUpdateRequest,
    create_request_to_model_data,
    update_request_to_model_data,
)


# ============================================================
# DATABASE REPOSITORY CONTRACT
# ============================================================
#
# IMPORTANT:
#
# Firebase/database implementation DOES NOT belong inside
# alert_service.py.
#
# Member 4 will provide the concrete database implementation.
#
# Architecture:
#
# routes/alerts.py
#       |
#       v
# alert_service.py
#       |
#       v
# AlertRepository
#       |
#       v
# Member 4 database layer
#       |
#       v
# Firebase
#
# This keeps our backend linked without hard-coding Firebase
# code into the API layer.
# ============================================================


class AlertRepository(Protocol):
    """
    Contract required from the database layer for alerts.
    """

    async def create_alert(
        self,
        alert: Alert,
    ) -> Alert:
        """
        Store a new alert.
        """
        ...

    async def get_alert_by_id(
        self,
        alert_id: str,
    ) -> Optional[Alert]:
        """
        Retrieve an alert by ID.
        """
        ...

    async def list_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        audience: Optional[AlertAudience] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Alert]:
        """
        Retrieve alerts using optional filters.
        """
        ...

    async def update_alert(
        self,
        alert_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Alert]:
        """
        Update an existing alert.
        """
        ...

    async def delete_alert(
        self,
        alert_id: str,
    ) -> bool:
        """
        Delete an alert.
        """
        ...


# ============================================================
# NOTIFICATION SERVICE CONTRACT
# ============================================================
#
# Notification implementation stays in:
#
# services/notification_service.py
#
# This service only calls the notification layer.
#
# Later it can be connected to Firebase Cloud Messaging or
# another notification mechanism by the team.
# ============================================================


class AlertNotificationService(Protocol):
    """
    Contract for sending alert notifications.
    """

    async def send_alert_notification(
        self,
        alert: Alert,
    ) -> Any:
        """
        Send an alert notification to the intended audience.
        """
        ...

    async def cancel_alert_notification(
        self,
        alert: Alert,
    ) -> Any:
        """
        Cancel/revoke an alert notification if supported.
        """
        ...


# ============================================================
# SERVICE INSTANCES
# ============================================================

_alert_repository: Optional[
    AlertRepository
] = None

_alert_notification_service: Optional[
    AlertNotificationService
] = None


# ============================================================
# CONFIGURE REPOSITORY
# ============================================================


def configure_alert_repository(
    repository: AlertRepository,
) -> None:
    """
    Register the concrete alert repository.

    Member 4's Firebase implementation can be injected here.
    """

    global _alert_repository

    if repository is None:
        raise ValueError(
            "Alert repository cannot be None."
        )

    _alert_repository = repository


# ============================================================
# GET REPOSITORY
# ============================================================


def get_alert_repository() -> AlertRepository:
    """
    Return the configured alert repository.
    """

    if _alert_repository is None:

        raise RuntimeError(
            "Alert repository is not configured."
        )

    return _alert_repository


# ============================================================
# CONFIGURE NOTIFICATION SERVICE
# ============================================================


def configure_alert_notification_service(
    notification_service: AlertNotificationService,
) -> None:
    """
    Register the concrete notification service.
    """

    global _alert_notification_service

    if notification_service is None:
        raise ValueError(
            "Alert notification service cannot be None."
        )

    _alert_notification_service = (
        notification_service
    )


# ============================================================
# GET NOTIFICATION SERVICE
# ============================================================


def get_alert_notification_service() -> Optional[
    AlertNotificationService
]:
    """
    Return the configured notification service.

    None is allowed so that database operations can still be
    performed while notification integration is unavailable.
    """

    return _alert_notification_service


# ============================================================
# CREATE ALERT
# ============================================================


async def create_alert(
    payload: AlertCreateRequest,
    creator_id: str,
) -> Alert:
    """
    Create and persist a new emergency alert.

    Flow:

        Request
           |
           v
        Schema
           |
           v
        Authenticated creator
           |
           v
        Alert model
           |
           +--------------+
           |              |
           v              v
       Database       Notification
           |              |
           +-------+------+
                   |
                   v
                Alert
    """

    # --------------------------------------------------------
    # Validate creator
    # --------------------------------------------------------

    if not creator_id:

        raise ValueError(
            "Authenticated creator ID is required."
        )

    # --------------------------------------------------------
    # Convert request to internal model data
    # --------------------------------------------------------

    data = create_request_to_model_data(
        payload=payload,
        created_by=creator_id,
    )

    # --------------------------------------------------------
    # Generate alert ID
    # --------------------------------------------------------

    alert_id = generate_alert_id(
        creator_id
    )

    # --------------------------------------------------------
    # Build Alert object
    # --------------------------------------------------------

    alert = build_alert(
        alert_id=alert_id,
        created_by=data["created_by"],
        title=data["title"],
        message=data["message"],
        alert_type=data["alert_type"],
        severity=data["severity"],
        audience=data["audience"],
        location=data["location"],
        status=AlertStatus.ACTIVE,
        expires_at=data.get(
            "expires_at"
        ),
    )

    # --------------------------------------------------------
    # Persist first
    # --------------------------------------------------------
    #
    # Database should be the source of truth.
    #
    # Notification is sent only after successful persistence.
    # --------------------------------------------------------

    repository = get_alert_repository()

    stored_alert = (
        await repository.create_alert(
            alert
        )
    )

    # --------------------------------------------------------
    # Send notification
    # --------------------------------------------------------

    notification_service = (
        get_alert_notification_service()
    )

    if notification_service is not None:

        try:

            await notification_service.send_alert_notification(
                stored_alert
            )

        except Exception:
            # ------------------------------------------------
            # Alert already exists in database.
            #
            # Notification failure should not silently remove
            # the emergency alert.
            #
            # Logging can be added later.
            # ------------------------------------------------
            pass

    return stored_alert


# ============================================================
# GET ALERT
# ============================================================


async def get_alert(
    alert_id: str,
) -> Optional[Alert]:
    """
    Retrieve one alert by ID.
    """

    if not alert_id:

        raise ValueError(
            "Alert ID is required."
        )

    repository = get_alert_repository()

    alert = await repository.get_alert_by_id(
        alert_id
    )

    return alert


# ============================================================
# LIST ALERTS
# ============================================================


async def list_alerts(
    alert_type: Optional[AlertType] = None,
    severity: Optional[AlertSeverity] = None,
    audience: Optional[AlertAudience] = None,
    status: Optional[AlertStatus] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Alert]:
    """
    Retrieve alerts with optional filters.
    """

    # --------------------------------------------------------
    # Pagination validation
    # --------------------------------------------------------

    if limit < 1:

        raise ValueError(
            "Limit must be at least 1."
        )

    if limit > 100:

        raise ValueError(
            "Limit cannot exceed 100."
        )

    if offset < 0:

        raise ValueError(
            "Offset cannot be negative."
        )

    repository = get_alert_repository()

    alerts = await repository.list_alerts(
        alert_type=alert_type,
        severity=severity,
        audience=audience,
        status=status,
        limit=limit,
        offset=offset,
    )

    # --------------------------------------------------------
    # Automatically mark expired active alerts.
    #
    # We do not need to immediately persist this state here.
    # The repository/database can handle expiry separately.
    # --------------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    for alert in alerts:

        if (
            alert.status == AlertStatus.ACTIVE
            and alert.expires_at is not None
            and alert.expires_at <= now
        ):

            alert.status = (
                AlertStatus.EXPIRED
            )

    return alerts


# ============================================================
# LIST ACTIVE ALERTS
# ============================================================


async def list_active_alerts(
    audience: Optional[
        AlertAudience
    ] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Alert]:
    """
    Retrieve only currently active alerts.

    This is useful for the frontend alert dashboard.
    """

    alerts = await list_alerts(
        audience=audience,
        status=AlertStatus.ACTIVE,
        limit=limit,
        offset=offset,
    )

    return [
        alert
        for alert in alerts
        if is_alert_active(alert)
    ]


# ============================================================
# UPDATE ALERT
# ============================================================


async def update_alert(
    alert_id: str,
    payload: AlertUpdateRequest,
    requester_id: str,
) -> Optional[Alert]:
    """
    Update an existing alert.

    The requester must be the creator of the alert.
    """

    if not alert_id:

        raise ValueError(
            "Alert ID is required."
        )

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    # --------------------------------------------------------
    # Get existing alert
    # --------------------------------------------------------

    alert = await get_alert(
        alert_id
    )

    if alert is None:
        return None

    # --------------------------------------------------------
    # Ownership
    # --------------------------------------------------------

    if alert.created_by != requester_id:

        raise PermissionError(
            "You do not have permission to update this alert."
        )

    # --------------------------------------------------------
    # Do not modify expired/cancelled alerts normally.
    # --------------------------------------------------------

    if alert.status in {
        AlertStatus.EXPIRED,
        AlertStatus.CANCELLED,
    }:

        raise ValueError(
            "Expired or cancelled alerts cannot be updated."
        )

    # --------------------------------------------------------
    # Extract update fields
    # --------------------------------------------------------

    updates = update_request_to_model_data(
        payload
    )

    if not updates:

        raise ValueError(
            "No alert fields were provided for update."
        )

    # --------------------------------------------------------
    # Validate status transition
    # --------------------------------------------------------

    if "status" in updates:

        validate_alert_status_transition(
            current_status=alert.status,
            new_status=updates["status"],
        )

    # --------------------------------------------------------
    # Updated timestamp
    # --------------------------------------------------------

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    # --------------------------------------------------------
    # Cancelled timestamp
    # --------------------------------------------------------

    if (
        updates.get("status")
        == AlertStatus.CANCELLED
    ):

        updates["cancelled_at"] = (
            datetime.now(
                timezone.utc
            )
        )

    # --------------------------------------------------------
    # Persist
    # --------------------------------------------------------

    repository = get_alert_repository()

    updated_alert = (
        await repository.update_alert(
            alert_id,
            updates,
        )
    )

    # --------------------------------------------------------
    # Notify about updated alert
    # --------------------------------------------------------

    if updated_alert is not None:

        notification_service = (
            get_alert_notification_service()
        )

        if notification_service is not None:

            try:

                await notification_service.send_alert_notification(
                    updated_alert
                )

            except Exception:
                pass

    return updated_alert


# ============================================================
# ACTIVATE ALERT
# ============================================================


async def activate_alert(
    alert_id: str,
    requester_id: str,
) -> Optional[Alert]:
    """
    Activate an existing draft alert.
    """

    return await update_alert_status(
        alert_id=alert_id,
        new_status=AlertStatus.ACTIVE,
        requester_id=requester_id,
    )


# ============================================================
# CANCEL ALERT
# ============================================================


async def cancel_alert(
    alert_id: str,
    requester_id: str,
) -> Optional[Alert]:
    """
    Cancel an active alert.
    """

    alert = await get_alert(
        alert_id
    )

    if alert is None:
        return None

    if alert.created_by != requester_id:

        raise PermissionError(
            "You do not have permission to cancel this alert."
        )

    if alert.status == AlertStatus.CANCELLED:

        return alert

    if alert.status == AlertStatus.EXPIRED:

        raise ValueError(
            "An expired alert cannot be cancelled."
        )

    now = datetime.now(
        timezone.utc
    )

    updates = {
        "status": AlertStatus.CANCELLED,
        "cancelled_at": now,
        "updated_at": now,
    }

    repository = get_alert_repository()

    cancelled_alert = (
        await repository.update_alert(
            alert_id,
            updates,
        )
    )

    # --------------------------------------------------------
    # Notify notification layer
    # --------------------------------------------------------

    if cancelled_alert is not None:

        notification_service = (
            get_alert_notification_service()
        )

        if notification_service is not None:

            try:

                await notification_service.cancel_alert_notification(
                    cancelled_alert
                )

            except Exception:
                pass

    return cancelled_alert


# ============================================================
# UPDATE ALERT STATUS
# ============================================================


async def update_alert_status(
    alert_id: str,
    new_status: AlertStatus,
    requester_id: str,
) -> Optional[Alert]:
    """
    Update alert status through a controlled operation.
    """

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    alert = await get_alert(
        alert_id
    )

    if alert is None:
        return None

    if alert.created_by != requester_id:

        raise PermissionError(
            "You do not have permission to update this alert."
        )

    validate_alert_status_transition(
        current_status=alert.status,
        new_status=new_status,
    )

    now = datetime.now(
        timezone.utc
    )

    updates: Dict[str, Any] = {
        "status": new_status,
        "updated_at": now,
    }

    if new_status == AlertStatus.CANCELLED:

        updates["cancelled_at"] = now

    repository = get_alert_repository()

    updated_alert = (
        await repository.update_alert(
            alert_id,
            updates,
        )
    )

    # --------------------------------------------------------
    # Notification action
    # --------------------------------------------------------

    if updated_alert is not None:

        notification_service = (
            get_alert_notification_service()
        )

        if notification_service is not None:

            try:

                if (
                    new_status
                    == AlertStatus.ACTIVE
                ):

                    await notification_service.send_alert_notification(
                        updated_alert
                    )

                elif (
                    new_status
                    == AlertStatus.CANCELLED
                ):

                    await notification_service.cancel_alert_notification(
                        updated_alert
                    )

            except Exception:
                pass

    return updated_alert


# ============================================================
# DELETE ALERT
# ============================================================


async def delete_alert(
    alert_id: str,
    requester_id: str,
) -> bool:
    """
    Delete an alert after ownership validation.

    Active alerts are protected from normal deletion.
    """

    if not alert_id:

        raise ValueError(
            "Alert ID is required."
        )

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    alert = await get_alert(
        alert_id
    )

    if alert is None:
        return False

    if alert.created_by != requester_id:

        raise PermissionError(
            "You do not have permission to delete this alert."
        )

    # --------------------------------------------------------
    # Active alerts should be cancelled rather than silently
    # deleted.
    # --------------------------------------------------------

    if alert.status == AlertStatus.ACTIVE:

        raise ValueError(
            "Active alerts cannot be deleted. "
            "Cancel the alert instead."
        )

    repository = get_alert_repository()

    return await repository.delete_alert(
        alert_id
    )


# ============================================================
# EXPIRE ALERT
# ============================================================


async def expire_alert(
    alert_id: str,
) -> Optional[Alert]:
    """
    Mark an alert as expired.

    This operation can later be called by a scheduled/background
    process.
    """

    alert = await get_alert(
        alert_id
    )

    if alert is None:
        return None

    if alert.status != AlertStatus.ACTIVE:

        return alert

    if alert.expires_at is None:

        return alert

    now = datetime.now(
        timezone.utc
    )

    if alert.expires_at > now:

        return alert

    updates = {
        "status": AlertStatus.EXPIRED,
        "updated_at": now,
    }

    repository = get_alert_repository()

    expired_alert = (
        await repository.update_alert(
            alert_id,
            updates,
        )
    )

    return expired_alert


# ============================================================
# EXPIRE ALL DUE ALERTS
# ============================================================


async def expire_due_alerts(
    limit: int = 100,
) -> List[Alert]:
    """
    Find active alerts that have passed their expiry time and
    mark them as expired.

    This is designed for future scheduled/background execution.
    """

    if limit < 1:
        raise ValueError(
            "Limit must be at least 1."
        )

    if limit > 500:
        raise ValueError(
            "Limit cannot exceed 500."
        )

    repository = get_alert_repository()

    alerts = await repository.list_alerts(
        status=AlertStatus.ACTIVE,
        limit=limit,
        offset=0,
    )

    now = datetime.now(
        timezone.utc
    )

    expired_alerts: List[Alert] = []

    for alert in alerts:

        if (
            alert.expires_at is not None
            and alert.expires_at <= now
        ):

            updated_alert = (
                await repository.update_alert(
                    alert.id,
                    {
                        "status": AlertStatus.EXPIRED,
                        "updated_at": now,
                    },
                )
            )

            if updated_alert is not None:

                expired_alerts.append(
                    updated_alert
                )

    return expired_alerts


# ============================================================
# STATUS TRANSITION VALIDATION
# ============================================================


def validate_alert_status_transition(
    current_status: AlertStatus,
    new_status: AlertStatus,
) -> None:
    """
    Validate alert lifecycle transitions.

    Allowed flow:

        draft
          ↓
        active
          ↓
        expired

    or:

        active
          ↓
        cancelled
    """

    if current_status == new_status:
        return

    allowed_transitions = {
        AlertStatus.DRAFT: {
            AlertStatus.ACTIVE,
            AlertStatus.CANCELLED,
        },

        AlertStatus.ACTIVE: {
            AlertStatus.EXPIRED,
            AlertStatus.CANCELLED,
        },

        AlertStatus.EXPIRED: set(),

        AlertStatus.CANCELLED: set(),
    }

    allowed = allowed_transitions.get(
        current_status,
        set(),
    )

    if new_status not in allowed:

        raise ValueError(
            "Invalid alert status transition: "
            f"{current_status.value} -> "
            f"{new_status.value}"
        )


# ============================================================
# GENERATE ALERT ID
# ============================================================


def generate_alert_id(
    creator_id: str,
) -> str:
    """
    Generate an application-level alert ID.

    Firebase may replace this with its own document ID in the
    concrete repository implementation.
    """

    import hashlib
    import uuid

    if not creator_id:

        raise ValueError(
            "Creator ID is required."
        )

    timestamp = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    raw_value = (
        f"{creator_id}:"
        f"{timestamp}:"
        f"{uuid.uuid4()}"
    )

    digest = hashlib.sha256(
        raw_value.encode(
            "utf-8"
        )
    ).hexdigest()

    return f"alert_{digest[:24]}"


# ============================================================
# FILTER CONVERSION
# ============================================================


def filter_request_to_service_args(
    filters: AlertFilterRequest,
) -> Dict[str, Any]:
    """
    Convert filter schema into service arguments.
    """

    return {
        "alert_type": filters.alert_type,
        "severity": filters.severity,
        "audience": filters.audience,
        "status": filters.status,
        "limit": filters.limit,
        "offset": filters.offset,
    }


# ============================================================
# ALERT OWNERSHIP CHECK
# ============================================================


def user_owns_alert(
    alert: Alert,
    user_id: str,
) -> bool:
    """
    Check whether the supplied user created the alert.
    """

    if not user_id:
        return False

    return (
        alert.created_by
        == user_id
    )


# ============================================================
# ALERT PRIORITY CHECK
# ============================================================


def is_critical_alert(
    alert: Alert,
) -> bool:
    """
    Determine whether an alert is critical.
    """

    return (
        alert.severity
        == AlertSeverity.CRITICAL
    )


# ============================================================
# PUBLIC ALERT DATA
# ============================================================


def to_public_alert(
    alert: Alert,
) -> dict:
    """
    Convert an Alert model to JSON-safe public data.
    """

    return {
        "id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "alert_type": alert.alert_type.value,
        "severity": alert.severity.value,
        "audience": alert.audience.value,
        "location": (
            alert.location.model_dump(
                mode="json"
            )
            if alert.location
            else None
        ),
        "status": alert.status.value,
        "created_at": (
            alert.created_at.isoformat()
        ),
        "updated_at": (
            alert.updated_at.isoformat()
        ),
        "expires_at": (
            alert.expires_at.isoformat()
            if alert.expires_at
            else None
        ),
        "cancelled_at": (
            alert.cancelled_at.isoformat()
            if alert.cancelled_at
            else None
        ),
    }