from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.alert import (
    Alert,
    AlertAudience,
    AlertListItem,
    AlertLocation,
    AlertSeverity,
    AlertStatus,
    AlertType,
)


# ============================================================
# ALERT LOCATION REQUEST
# ============================================================

class AlertLocationRequest(BaseModel):
    """
    Optional location information supplied with an alert.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    building: Optional[str] = Field(
        default=None,
        max_length=200,
    )

    floor: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    room: Optional[str] = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# CREATE ALERT REQUEST
# ============================================================

class AlertCreateRequest(BaseModel):
    """
    Request body for:

        POST /alerts

    IMPORTANT:
        created_by is NOT accepted from the frontend.

    It must come from the authenticated backend user.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Alert title.",
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Alert message.",
    )

    alert_type: AlertType = Field(
        default=AlertType.EMERGENCY,
    )

    severity: AlertSeverity = Field(
        default=AlertSeverity.MEDIUM,
    )

    audience: AlertAudience = Field(
        default=AlertAudience.ALL,
    )

    location: Optional[
        AlertLocationRequest
    ] = None

    expires_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Alert title cannot be empty."
            )

        return value

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Alert message cannot be empty."
            )

        return value


# ============================================================
# UPDATE ALERT REQUEST
# ============================================================

class AlertUpdateRequest(BaseModel):
    """
    Partial update contract for future alert-management
    operations.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    message: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=5000,
    )

    alert_type: Optional[
        AlertType
    ] = None

    severity: Optional[
        AlertSeverity
    ] = None

    audience: Optional[
        AlertAudience
    ] = None

    location: Optional[
        AlertLocationRequest
    ] = None

    status: Optional[
        AlertStatus
    ] = None

    expires_at: Optional[
        datetime
    ] = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Alert title cannot be empty."
            )

        return value

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Alert message cannot be empty."
            )

        return value


# ============================================================
# ALERT RESPONSE
# ============================================================

class AlertResponse(BaseModel):
    """
    Complete public alert response.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    title: str

    message: str

    alert_type: AlertType

    severity: AlertSeverity

    audience: AlertAudience

    location: Optional[AlertLocation]

    status: AlertStatus

    created_at: datetime

    updated_at: datetime

    expires_at: Optional[datetime]

    cancelled_at: Optional[datetime]


# ============================================================
# ALERT LIST ITEM RESPONSE
# ============================================================

class AlertListItemResponse(BaseModel):
    """
    Lightweight alert representation used by GET /alerts.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    title: str

    message: str

    alert_type: AlertType

    severity: AlertSeverity

    audience: AlertAudience

    location: Optional[AlertLocation]

    status: AlertStatus

    created_at: datetime

    updated_at: datetime

    expires_at: Optional[datetime]


# ============================================================
# ALERT LIST RESPONSE
# ============================================================

class AlertListResponse(BaseModel):
    """
    Response contract for:

        GET /alerts
    """

    alerts: List[
        AlertListItemResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# ALERT CREATE RESPONSE
# ============================================================

class AlertCreateResponse(BaseModel):
    """
    Response contract for:

        POST /alerts
    """

    alert: AlertResponse


# ============================================================
# ALERT DETAIL RESPONSE
# ============================================================

class AlertDetailResponse(BaseModel):
    """
    Detailed alert response wrapper.
    """

    alert: AlertResponse


# ============================================================
# ALERT STATUS RESPONSE
# ============================================================

class AlertStatusResponse(BaseModel):
    """
    Lightweight alert status response.
    """

    id: str

    status: AlertStatus

    severity: AlertSeverity

    updated_at: datetime


# ============================================================
# ALERT FILTER REQUEST
# ============================================================

class AlertFilterRequest(BaseModel):
    """
    Internal filter contract for alert listing.

    This can later be populated from query parameters.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    alert_type: Optional[
        AlertType
    ] = None

    severity: Optional[
        AlertSeverity
    ] = None

    audience: Optional[
        AlertAudience
    ] = None

    status: Optional[
        AlertStatus
    ] = None

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# LOCATION CONVERTER
# ============================================================

def location_request_to_model(
    location: Optional[
        AlertLocationRequest
    ],
) -> Optional[AlertLocation]:
    """
    Convert API location schema into the domain model.
    """

    if location is None:
        return None

    return AlertLocation(
        latitude=location.latitude,
        longitude=location.longitude,
        address=location.address,
        building=location.building,
        floor=location.floor,
        room=location.room,
    )


# ============================================================
# CREATE REQUEST -> MODEL DATA
# ============================================================

def create_request_to_model_data(
    payload: AlertCreateRequest,
    created_by: str,
) -> dict:
    """
    Convert the API request into data expected by the
    alert service.

    created_by comes from authentication.
    """

    if not created_by:
        raise ValueError(
            "Authenticated creator ID is required."
        )

    return {
        "created_by": created_by,
        "title": payload.title,
        "message": payload.message,
        "alert_type": payload.alert_type,
        "severity": payload.severity,
        "audience": payload.audience,
        "location": location_request_to_model(
            payload.location
        ),
        "expires_at": payload.expires_at,
    }


# ============================================================
# UPDATE REQUEST -> MODEL DATA
# ============================================================

def update_request_to_model_data(
    payload: AlertUpdateRequest,
) -> dict:
    """
    Extract only fields supplied by the client.
    """

    data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "location" in data:

        location = data["location"]

        if isinstance(
            location,
            AlertLocationRequest,
        ):
            data["location"] = (
                location_request_to_model(
                    location
                )
            )

    return data


# ============================================================
# ALERT RESPONSE BUILDER
# ============================================================

def build_alert_response(
    alert: Alert,
) -> AlertResponse:
    """
    Convert Alert model into API response.
    """

    return AlertResponse.model_validate(
        alert
    )


# ============================================================
# ALERT LIST ITEM BUILDER
# ============================================================

def build_alert_list_item(
    alert: Alert,
) -> AlertListItemResponse:
    """
    Convert an Alert into a lightweight list item.
    """

    return AlertListItemResponse.model_validate(
        alert
    )


# ============================================================
# ALERT LIST RESPONSE BUILDER
# ============================================================

def build_alert_list_response(
    alerts: List[Alert],
) -> AlertListResponse:
    """
    Build the complete response for GET /alerts.
    """

    items = [
        build_alert_list_item(
            alert
        )
        for alert in alerts
    ]

    return AlertListResponse(
        alerts=items,
        total=len(items),
    )


# ============================================================
# ALERT CREATE RESPONSE BUILDER
# ============================================================

def build_alert_create_response(
    alert: Alert,
) -> AlertCreateResponse:
    """
    Build response for POST /alerts.
    """

    return AlertCreateResponse(
        alert=build_alert_response(
            alert
        )
    )


# ============================================================
# ALERT DETAIL RESPONSE BUILDER
# ============================================================

def build_alert_detail_response(
    alert: Alert,
) -> AlertDetailResponse:
    """
    Build detailed alert response.
    """

    return AlertDetailResponse(
        alert=build_alert_response(
            alert
        )
    )


# ============================================================
# ALERT STATUS RESPONSE BUILDER
# ============================================================

def build_alert_status_response(
    alert: Alert,
) -> AlertStatusResponse:
    """
    Build lightweight status response.
    """

    return AlertStatusResponse(
        id=alert.id,
        status=alert.status,
        severity=alert.severity,
        updated_at=alert.updated_at,
    )


# ============================================================
# CHECK EMPTY UPDATE
# ============================================================

def has_alert_updates(
    payload: AlertUpdateRequest,
) -> bool:
    """
    Check whether at least one update field was supplied.
    """

    return bool(
        payload.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )
    )