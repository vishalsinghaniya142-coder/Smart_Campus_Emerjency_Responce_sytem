from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# SOS STATUS
# ============================================================

class SOSStatus(str, Enum):
    """
    Current status of an SOS request.
    """

    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


# ============================================================
# SOS LOCATION
# ============================================================

class SOSLocation(BaseModel):
    """
    Location supplied with an SOS request.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# CREATE SOS REQUEST
# ============================================================

class SOSCreateRequest(BaseModel):
    """
    Request contract for:

        POST /sos
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    location: SOSLocation

    message: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


# ============================================================
# SOS RESPONSE
# ============================================================

class SOSResponse(BaseModel):
    """
    Complete SOS API response.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    user_id: str

    location: SOSLocation

    message: Optional[str] = None

    status: SOSStatus

    created_at: datetime

    updated_at: datetime


# ============================================================
# SOS CREATE RESPONSE
# ============================================================

class SOSCreateResponse(BaseModel):
    """
    Response returned after an SOS is created.
    """

    sos: SOSResponse


# ============================================================
# SOS STATUS RESPONSE
# ============================================================

class SOSStatusResponse(BaseModel):
    """
    Lightweight SOS status response.
    """

    id: str

    status: SOSStatus

    updated_at: datetime


# ============================================================
# SOS UPDATE REQUEST
# ============================================================

class SOSUpdateRequest(BaseModel):
    """
    Request used for changing the SOS state.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    status: SOSStatus


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_sos_location(
    location: SOSLocation,
) -> SOSLocation:
    """
    Validate and return SOS location.
    """

    if location.latitude is None:
        raise ValueError(
            "SOS latitude is required."
        )

    if location.longitude is None:
        raise ValueError(
            "SOS longitude is required."
        )

    return location


# ============================================================
# REQUEST -> SERVICE DATA
# ============================================================

def create_sos_request_to_data(
    payload: SOSCreateRequest,
    user_id: str,
) -> dict:
    """
    Convert API request into service-layer data.

    user_id always comes from authenticated backend context.
    It must never come from the frontend request body.
    """

    if not user_id:
        raise ValueError(
            "Authenticated user ID is required."
        )

    validate_sos_location(
        payload.location
    )

    return {
        "user_id": user_id,
        "location": payload.location,
        "message": payload.message,
        "status": SOSStatus.ACTIVE,
    }


# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_sos_response(
    sos,
) -> SOSResponse:
    """
    Convert an internal SOS object into API response.
    """

    return SOSResponse.model_validate(
        sos
    )


# ============================================================
# CREATE RESPONSE BUILDER
# ============================================================

def build_sos_create_response(
    sos,
) -> SOSCreateResponse:
    """
    Build POST /sos response.
    """

    return SOSCreateResponse(
        sos=build_sos_response(
            sos
        )
    )


# ============================================================
# STATUS RESPONSE BUILDER
# ============================================================

def build_sos_status_response(
    sos,
) -> SOSStatusResponse:
    """
    Build lightweight SOS status response.
    """

    return SOSStatusResponse(
        id=sos.id,
        status=sos.status,
        updated_at=sos.updated_at,
    )