from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.models.sos import (
    SOS,
    build_sos,
    sos_from_document,
    sos_to_document,
    update_sos_status,
)

from app.schemas.sos_schema import (
    SOSCreateRequest,
    SOSStatus,
    SOSUpdateRequest,
    build_sos_response,
    create_sos_request_to_data,
)


# ============================================================
# SOS REPOSITORY CONTRACT
# ============================================================

class SOSRepository(Protocol):
    """
    Database contract for SOS operations.

    Member 2 defines the contract.

    Member 4 can later provide the Firebase implementation.
    """

    async def create_sos(
        self,
        sos: SOS,
    ) -> SOS:
        ...

    async def get_sos_by_id(
        self,
        sos_id: str,
    ) -> Optional[SOS]:
        ...

    async def list_sos_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SOS]:
        ...

    async def update_sos(
        self,
        sos_id: str,
        updates: Dict[str, Any],
    ) -> Optional[SOS]:
        ...


# ============================================================
# NOTIFICATION CONTRACT
# ============================================================

class SOSNotificationService(Protocol):
    """
    Contract for SOS notification handling.

    Concrete implementation can be connected later.
    """

    async def send_sos_notification(
        self,
        sos: SOS,
    ) -> Any:
        ...


# ============================================================
# SERVICE STATE
# ============================================================

_sos_repository: Optional[
    SOSRepository
] = None

_sos_notification_service: Optional[
    SOSNotificationService
] = None


# ============================================================
# CONFIGURE REPOSITORY
# ============================================================

def configure_sos_repository(
    repository: SOSRepository,
) -> None:
    """
    Register the database repository implementation.
    """

    global _sos_repository

    if repository is None:
        raise ValueError(
            "SOS repository cannot be None."
        )

    _sos_repository = repository


# ============================================================
# GET REPOSITORY
# ============================================================

def get_sos_repository() -> SOSRepository:
    """
    Return the configured SOS repository.

    Until Member 4 connects Firebase, attempting an actual
    database operation will raise RuntimeError.
    """

    if _sos_repository is None:
        raise RuntimeError(
            "SOS repository is not configured."
        )

    return _sos_repository


# ============================================================
# CONFIGURE NOTIFICATION SERVICE
# ============================================================

def configure_sos_notification_service(
    notification_service: SOSNotificationService,
) -> None:
    """
    Register notification implementation.
    """

    global _sos_notification_service

    if notification_service is None:
        raise ValueError(
            "SOS notification service cannot be None."
        )

    _sos_notification_service = (
        notification_service
    )


# ============================================================
# GET NOTIFICATION SERVICE
# ============================================================

def get_sos_notification_service() -> Optional[
    SOSNotificationService
]:
    """
    Return configured notification service.
    """

    return _sos_notification_service


# ============================================================
# GENERATE SOS ID
# ============================================================

def generate_sos_id(
    user_id: str,
) -> str:
    """
    Generate an application-level SOS ID.
    """

    import hashlib
    import uuid

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    raw_value = (
        f"{user_id}:"
        f"{timestamp}:"
        f"{uuid.uuid4()}"
    )

    digest = hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()

    return f"sos_{digest[:24]}"


# ============================================================
# CREATE SOS
# ============================================================

async def create_sos(
    payload: SOSCreateRequest,
    user_id: str,
) -> SOS:
    """
    Create an SOS request.

    Flow:

        Route
          ↓
        Schema
          ↓
        Service
          ↓
        Repository contract
          ↓
        Firebase / database
    """

    if payload is None:
        raise ValueError(
            "SOS request payload is required."
        )

    if not user_id:
        raise ValueError(
            "Authenticated user ID is required."
        )

    # --------------------------------------------------------
    # Convert request into service data
    # --------------------------------------------------------

    data = create_sos_request_to_data(
        payload=payload,
        user_id=user_id,
    )

    # --------------------------------------------------------
    # Build internal model
    # --------------------------------------------------------

    status_value = data["status"]

    if isinstance(
        status_value,
        SOSStatus,
    ):
        status_value = status_value.value

    sos = build_sos(
        sos_id=generate_sos_id(
            user_id
        ),
        user_id=data["user_id"],
        location=data["location"],
        message=data["message"],
        status=status_value,
    )

    # --------------------------------------------------------
    # Get database repository
    # --------------------------------------------------------

    repository = get_sos_repository()

    # --------------------------------------------------------
    # Persist
    # --------------------------------------------------------

    stored_sos = await repository.create_sos(
        sos
    )

    # --------------------------------------------------------
    # Optional notification
    # --------------------------------------------------------

    notification_service = (
        get_sos_notification_service()
    )

    if notification_service is not None:

        try:
            await notification_service.send_sos_notification(
                stored_sos
            )
        except Exception:
            # Notification failure should not remove the SOS.
            pass

    return stored_sos


# ============================================================
# GET SOS
# ============================================================

async def get_sos(
    sos_id: str,
) -> Optional[SOS]:
    """
    Retrieve an SOS by ID.
    """

    if not sos_id:
        raise ValueError(
            "SOS ID is required."
        )

    repository = get_sos_repository()

    return await repository.get_sos_by_id(
        sos_id
    )


# ============================================================
# LIST USER SOS
# ============================================================

async def list_user_sos(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[SOS]:
    """
    Retrieve SOS requests belonging to a user.
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

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

    repository = get_sos_repository()

    return await repository.list_sos_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


# ============================================================
# UPDATE SOS
# ============================================================

async def update_sos(
    sos_id: str,
    payload: SOSUpdateRequest,
    requester_id: str,
) -> Optional[SOS]:
    """
    Update SOS status.
    """

    if not sos_id:
        raise ValueError(
            "SOS ID is required."
        )

    if not requester_id:
        raise ValueError(
            "Authenticated requester ID is required."
        )

    if payload is None:
        raise ValueError(
            "SOS update payload is required."
        )

    sos = await get_sos(
        sos_id
    )

    if sos is None:
        return None

    # --------------------------------------------------------
    # Ownership
    # --------------------------------------------------------

    if str(sos.user_id) != str(
        requester_id
    ):
        raise PermissionError(
            "You do not have permission to update this SOS."
        )

    # --------------------------------------------------------
    # Prevent invalid reactivation
    # --------------------------------------------------------

    if (
        sos.status in {
            SOSStatus.RESOLVED.value,
            SOSStatus.CANCELLED.value,
        }
        and payload.status
        == SOSStatus.ACTIVE
    ):
        raise ValueError(
            "A resolved or cancelled SOS "
            "cannot be reactivated."
        )

    # --------------------------------------------------------
    # Update model
    # --------------------------------------------------------

    updated_sos = update_sos_status(
        sos=sos,
        new_status=payload.status.value,
    )

    # --------------------------------------------------------
    # Database update
    # --------------------------------------------------------

    repository = get_sos_repository()

    return await repository.update_sos(
        sos_id=sos_id,
        updates={
            "status": updated_sos.status,
            "updated_at": updated_sos.updated_at,
        },
    )


# ============================================================
# RESOLVE SOS
# ============================================================

async def resolve_sos(
    sos_id: str,
    requester_id: str,
) -> Optional[SOS]:
    """
    Resolve an SOS.
    """

    return await update_sos(
        sos_id=sos_id,
        payload=SOSUpdateRequest(
            status=SOSStatus.RESOLVED
        ),
        requester_id=requester_id,
    )


# ============================================================
# CANCEL SOS
# ============================================================

async def cancel_sos(
    sos_id: str,
    requester_id: str,
) -> Optional[SOS]:
    """
    Cancel an SOS.
    """

    return await update_sos(
        sos_id=sos_id,
        payload=SOSUpdateRequest(
            status=SOSStatus.CANCELLED
        ),
        requester_id=requester_id,
    )


# ============================================================
# CHECK ACTIVE SOS
# ============================================================

async def has_active_sos(
    user_id: str,
) -> bool:
    """
    Check whether the user has an active SOS.
    """

    sos_requests = await list_user_sos(
        user_id=user_id,
        limit=100,
        offset=0,
    )

    return any(
        sos.status == SOSStatus.ACTIVE.value
        for sos in sos_requests
    )


# ============================================================
# PUBLIC RESPONSE
# ============================================================

def to_public_sos(
    sos: SOS,
) -> dict:
    """
    Convert SOS model to API-safe data.
    """

    response = build_sos_response(
        sos
    )

    return response.model_dump(
        mode="json"
    )


# ============================================================
# DATABASE DOCUMENT HELPERS
# ============================================================

def to_database_document(
    sos: SOS,
) -> dict:
    """
    Convert SOS to database-neutral document.

    Member 4's Firebase repository can use this.
    """

    return sos_to_document(
        sos
    )


def from_database_document(
    document: dict,
) -> SOS:
    """
    Convert database document into SOS model.
    """

    return sos_from_document(
        document
    )