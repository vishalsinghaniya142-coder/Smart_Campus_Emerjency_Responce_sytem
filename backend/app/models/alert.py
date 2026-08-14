from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# ALERT ENUMS
# ============================================================

class AlertType(str, Enum):
    """
    Type/category of emergency alert.
    """

    EMERGENCY = "emergency"
    FIRE = "fire"
    MEDICAL = "medical"
    SECURITY = "security"
    WEATHER = "weather"
    EVACUATION = "evacuation"
    SAFETY = "safety"
    SYSTEM = "system"
    OTHER = "other"


class AlertSeverity(str, Enum):
    """
    Severity of an alert.

    This represents the urgency of the notification.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """
    Lifecycle status of an alert.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AlertAudience(str, Enum):
    """
    Intended audience of an alert.
    """

    ALL = "all"
    STUDENTS = "students"
    STAFF = "staff"
    SECURITY = "security"
    ADMIN = "admin"


# ============================================================
# ALERT LOCATION
# ============================================================

class AlertLocation(BaseModel):
    """
    Optional geographic information attached to an alert.

    Maps/location processing is intentionally NOT implemented
    here.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitude associated with the alert.",
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitude associated with the alert.",
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable location.",
    )

    building: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Campus building.",
    )

    floor: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Building floor.",
    )

    room: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Room or specific area.",
    )


# ============================================================
# ALERT BASE
# ============================================================

class AlertBase(BaseModel):
    """
    Common fields shared by alert creation and alert records.
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
        examples=["Emergency evacuation notice"],
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Alert message.",
        examples=[
            "Please evacuate the academic block immediately."
        ],
    )

    alert_type: AlertType = Field(
        default=AlertType.EMERGENCY,
        description="Type of alert.",
    )

    severity: AlertSeverity = Field(
        default=AlertSeverity.MEDIUM,
        description="Alert severity.",
    )

    audience: AlertAudience = Field(
        default=AlertAudience.ALL,
        description="Intended alert audience.",
    )

    location: Optional[AlertLocation] = Field(
        default=None,
        description="Optional alert location.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        """
        Validate alert title.
        """

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
        """
        Validate alert message.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Alert message cannot be empty."
            )

        return value


# ============================================================
# ALERT CREATE MODEL
# ============================================================

class AlertCreate(BaseModel):
    """
    Internal model used when creating an alert.

    created_by must come from the authenticated backend
    context, not from an untrusted client field.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    created_by: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="ID of the user/admin creating the alert.",
    )

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=5000,
    )

    alert_type: AlertType = (
        AlertType.EMERGENCY
    )

    severity: AlertSeverity = (
        AlertSeverity.MEDIUM
    )

    audience: AlertAudience = (
        AlertAudience.ALL
    )

    location: Optional[AlertLocation] = None

    status: AlertStatus = (
        AlertStatus.ACTIVE
    )

    expires_at: Optional[datetime] = None


# ============================================================
# ALERT MODEL
# ============================================================

class Alert(BaseModel):
    """
    Complete backend representation of an emergency alert.

    Database persistence is intentionally outside this model.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique alert identifier.",
    )

    created_by: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="User/admin who created the alert.",
    )

    title: str

    message: str

    alert_type: AlertType

    severity: AlertSeverity

    audience: AlertAudience

    location: Optional[AlertLocation] = None

    status: AlertStatus = (
        AlertStatus.ACTIVE
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ),
    )

    expires_at: Optional[datetime] = None

    cancelled_at: Optional[datetime] = None


# ============================================================
# PUBLIC ALERT MODEL
# ============================================================

class AlertPublic(BaseModel):
    """
    Safe representation of an alert for frontend/API use.
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
# ALERT LIST ITEM
# ============================================================

class AlertListItem(BaseModel):
    """
    Lightweight representation used for GET /alerts lists.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    title: str

    alert_type: AlertType

    severity: AlertSeverity

    audience: AlertAudience

    status: AlertStatus

    created_at: datetime

    expires_at: Optional[datetime]


# ============================================================
# ALERT UPDATE MODEL
# ============================================================

class AlertUpdate(BaseModel):
    """
    Internal model for partial alert updates.
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

    alert_type: Optional[AlertType] = None

    severity: Optional[AlertSeverity] = None

    audience: Optional[AlertAudience] = None

    location: Optional[AlertLocation] = None

    status: Optional[AlertStatus] = None

    expires_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate optional updated title.
        """

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
        """
        Validate optional updated message.
        """

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Alert message cannot be empty."
            )

        return value


# ============================================================
# ALERT READ / ACKNOWLEDGEMENT MODEL
# ============================================================

class AlertReadReceipt(BaseModel):
    """
    Represents a user's acknowledgement/read state for an
    alert.

    This is kept as a domain model so that notification/read
    tracking can be added without changing the core Alert
    object.
    """

    alert_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    read_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ),
    )


# ============================================================
# ALERT CREATION HELPER
# ============================================================

def build_alert(
    alert_id: str,
    created_by: str,
    title: str,
    message: str,
    alert_type: AlertType = AlertType.EMERGENCY,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    audience: AlertAudience = AlertAudience.ALL,
    location: Optional[AlertLocation] = None,
    status: AlertStatus = AlertStatus.ACTIVE,
    expires_at: Optional[datetime] = None,
) -> Alert:
    """
    Build a complete Alert object.

    No database operation occurs here.
    """

    now = datetime.now(
        timezone.utc
    )

    return Alert(
        id=str(alert_id),
        created_by=str(created_by),
        title=title,
        message=message,
        alert_type=alert_type,
        severity=severity,
        audience=audience,
        location=location,
        status=status,
        created_at=now,
        updated_at=now,
        expires_at=expires_at,
    )


# ============================================================
# ALERT TO PUBLIC
# ============================================================

def alert_to_public(
    alert: Alert,
) -> AlertPublic:
    """
    Convert an Alert into its public representation.
    """

    return AlertPublic(
        id=alert.id,
        title=alert.title,
        message=alert.message,
        alert_type=alert.alert_type,
        severity=alert.severity,
        audience=alert.audience,
        location=alert.location,
        status=alert.status,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        expires_at=alert.expires_at,
        cancelled_at=alert.cancelled_at,
    )


# ============================================================
# ALERT LIST CONVERSION
# ============================================================

def alert_to_list_item(
    alert: Alert,
) -> AlertListItem:
    """
    Convert a complete alert to a lightweight list item.
    """

    return AlertListItem(
        id=alert.id,
        title=alert.title,
        alert_type=alert.alert_type,
        severity=alert.severity,
        audience=alert.audience,
        status=alert.status,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
    )


# ============================================================
# ALERT UPDATE DATA
# ============================================================

def get_alert_update_data(
    update: AlertUpdate,
) -> Dict[str, Any]:
    """
    Extract only fields supplied for a partial update.
    """

    return update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )


# ============================================================
# ALERT ACTIVE CHECK
# ============================================================

def is_alert_active(
    alert: Alert,
) -> bool:
    """
    Determine whether an alert is currently active.

    An alert with a past expiry time is considered inactive.
    """

    if alert.status != AlertStatus.ACTIVE:
        return False

    if (
        alert.expires_at is not None
        and alert.expires_at <= datetime.now(
            timezone.utc
        )
    ):
        return False

    return True


# ============================================================
# ALERT EXPIRED CHECK
# ============================================================

def is_alert_expired(
    alert: Alert,
) -> bool:
    """
    Determine whether an alert has expired.
    """

    if alert.expires_at is None:
        return False

    return (
        alert.expires_at
        <= datetime.now(
            timezone.utc
        )
    )


# ============================================================
# ALERT HIGH PRIORITY CHECK
# ============================================================

def is_high_priority_alert(
    alert: Alert,
) -> bool:
    """
    Determine whether an alert should be treated as
    high-priority.
    """

    return alert.severity in {
        AlertSeverity.HIGH,
        AlertSeverity.CRITICAL,
    }


# ============================================================
# ALERT STATUS TRANSITION
# ============================================================

def apply_alert_status(
    alert: Alert,
    new_status: AlertStatus,
) -> Alert:
    """
    Apply a status change without persisting it.

    Persistence remains the responsibility of alert_service.py.
    """

    now = datetime.now(
        timezone.utc
    )

    alert.status = new_status

    alert.updated_at = now

    if new_status == AlertStatus.CANCELLED:

        alert.cancelled_at = now

    elif new_status == AlertStatus.ACTIVE:

        alert.cancelled_at = None

    return alert


# ============================================================
# ALERT DOCUMENT CONVERSION
# ============================================================

def alert_to_document(
    alert: Alert,
) -> Dict[str, Any]:
    """
    Convert Alert into a database-neutral dictionary.

    Member 4's database layer can transform this into its
    Firebase document representation.
    """

    return alert.model_dump(
        mode="json"
    )


# ============================================================
# ALERT FROM DOCUMENT
# ============================================================

def alert_from_document(
    document: Dict[str, Any],
) -> Alert:
    """
    Convert a database document into an Alert model.
    """

    if not isinstance(
        document,
        dict,
    ):
        raise ValueError(
            "Alert document must be a dictionary."
        )

    if "id" not in document:

        raise ValueError(
            "Alert document must contain an ID."
        )

    return Alert.model_validate(
        document
    )