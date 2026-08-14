from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# SOS MODEL
# ============================================================

class SOS(BaseModel):
    """
    Internal SOS model.

    This model is intentionally independent from API schemas.
    Database/Firebase implementation is also kept outside this
    model and belongs to the repository/integration layer.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    # Location is kept schema-independent here.
    # SOS schema validates latitude/longitude.
    location: Any

    message: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    # Kept as string-compatible value so the model does not
    # import SOSStatus from sos_schema.py.
    status: str = "active"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ) )


# ============================================================
# SOS CREATE MODEL
# ============================================================

class SOSCreate(BaseModel):
    """
    Internal model used by the SOS service.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    location: Any

    message: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    status: str = "active"


# ============================================================
# SOS UPDATE MODEL
# ============================================================

class SOSUpdate(BaseModel):
    """
    Internal SOS status update model.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    status: str


# ============================================================
# BUILD SOS
# ============================================================

def build_sos(
    sos_id: str,
    user_id: str,
    location: Any,
    message: Optional[str] = None,
    status: Any = "active",
) -> SOS:
    """
    Build an SOS model without importing API schemas.
    """

    if not sos_id:
        raise ValueError(
            "SOS ID is required."
        )

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    now = datetime.now(
        timezone.utc
    )

    return SOS(
        id=str(sos_id),
        user_id=str(user_id),
        location=location,
        message=message,
        status=str(status),
        created_at=now,
        updated_at=now,
    )


# ============================================================
# SOS STATUS HELPERS
# ============================================================

def is_sos_active(
    sos: SOS,
) -> bool:
    """
    Check whether an SOS is active.
    """

    return str(sos.status) == "active"


def is_sos_resolved(
    sos: SOS,
) -> bool:
    """
    Check whether an SOS is resolved.
    """

    return str(sos.status) == "resolved"


def is_sos_cancelled(
    sos: SOS,
) -> bool:
    """
    Check whether an SOS is cancelled.
    """

    return str(sos.status) == "cancelled"


# ============================================================
# UPDATE STATUS
# ============================================================

def update_sos_status(
    sos: SOS,
    new_status: Any,
) -> SOS:
    """
    Update SOS lifecycle status.
    """

    sos.status = str(new_status)

    sos.updated_at = datetime.now(
        timezone.utc
    )

    return sos


# ============================================================
# DATABASE DOCUMENT
# ============================================================

def sos_to_document(
    sos: SOS,
) -> dict:
    """
    Convert SOS model into a database-neutral dictionary.
    """

    return sos.model_dump(
        mode="json"
    )


# ============================================================
# DOCUMENT -> SOS
# ============================================================

def sos_from_document(
    document: dict,
) -> SOS:
    """
    Convert a database document into an SOS model.
    """

    if not isinstance(
        document,
        dict,
    ):
        raise ValueError(
            "SOS document must be a dictionary."
        )

    if "id" not in document:
        raise ValueError(
            "SOS document must contain an ID."
        )

    return SOS.model_validate(
        document
    )