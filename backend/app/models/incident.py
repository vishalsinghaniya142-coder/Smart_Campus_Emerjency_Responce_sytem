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
# INCIDENT ENUMS
# ============================================================

class IncidentType(str, Enum):
    """
    Supported emergency incident categories.

    These values are kept stable because the frontend,
    backend, AI module and database layer may all exchange
    them.
    """

    FIRE = "fire"
    MEDICAL = "medical"
    ACCIDENT = "accident"
    SECURITY = "security"
    NATURAL_DISASTER = "natural_disaster"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    """
    Incident severity levels.

    AI prediction can later determine or suggest severity,
    but the model only represents the result.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """
    Lifecycle status of an emergency incident.
    """

    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


# ============================================================
# LOCATION MODEL
# ============================================================

class IncidentLocation(BaseModel):
    """
    Geographic location associated with an incident.

    Coordinates can later be consumed by Member 4's Maps
    services.

    This model does NOT implement map logic.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Incident latitude.",
        examples=[26.8467],
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Incident longitude.",
        examples=[80.9462],
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable incident address.",
        examples=["Campus Main Gate"],
    )

    building: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Campus building/location name.",
        examples=["Academic Block"],
    )

    floor: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Floor or level where incident occurred.",
        examples=["2nd Floor"],
    )

    room: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Room/area identifier.",
        examples=["Room 204"],
    )


# ============================================================
# INCIDENT IMAGE
# ============================================================

class IncidentImage(BaseModel):
    """
    Metadata for an image attached to an incident.

    The actual image file is not stored inside this model.

    Frontend:
        multipart upload

    Backend:
        receives file

    AI:
        image analysis

    Database/storage:
        stores appropriate file reference
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    url: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Stored image URL.",
    )

    storage_path: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Storage reference/path.",
    )

    filename: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Original image filename.",
    )

    content_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Image MIME type.",
    )


# ============================================================
# AI ANALYSIS RESULT
# ============================================================

class IncidentAIAnalysis(BaseModel):
    """
    Representation of AI analysis attached to an incident.

    IMPORTANT:

    This class only represents AI output.

    Gemini/ML implementation belongs to Member 3's ai/ folder.
    """

    model_config = ConfigDict(
        extra="allow",
    )

    detected_type: Optional[str] = Field(
        default=None,
        description="Emergency type detected by AI.",
    )

    severity: Optional[IncidentSeverity] = Field(
        default=None,
        description="Severity suggested by AI.",
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="AI confidence score.",
    )

    summary: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="AI-generated analysis summary.",
    )

    recommendations: List[str] = Field(
        default_factory=list,
        description="Emergency response recommendations.",
    )

    analyzed_at: Optional[datetime] = Field(
        default=None,
        description="Time when AI analysis was completed.",
    )


# ============================================================
# INCIDENT BASE
# ============================================================

class IncidentBase(BaseModel):
    """
    Common incident fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    incident_type: IncidentType = Field(
        ...,
        description="Type of emergency incident.",
        examples=["fire"],
    )

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short incident title.",
        examples=["Fire near laboratory"],
    )

    description: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Detailed incident description.",
    )

    location: IncidentLocation

    # --------------------------------------------------------
    # Optional severity
    # --------------------------------------------------------
    #
    # The user may report without knowing severity.
    # AI/service layer can later calculate or update it.
    # --------------------------------------------------------

    severity: Optional[IncidentSeverity] = Field(
        default=None,
        description="Incident severity.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        """
        Normalize incident title.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Incident title cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:
        """
        Normalize incident description.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Incident description cannot be empty."
            )

        return value


# ============================================================
# INCIDENT CREATE MODEL
# ============================================================

class IncidentCreate(BaseModel):
    """
    Internal model used when creating an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    reporter_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="ID of the user reporting the incident.",
    )

    incident_type: IncidentType

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        ...,
        min_length=3,
        max_length=5000,
    )

    location: IncidentLocation

    severity: Optional[IncidentSeverity] = None

    status: IncidentStatus = (
        IncidentStatus.REPORTED
    )

    images: List[IncidentImage] = Field(
        default_factory=list,
    )

    ai_analysis: Optional[
        IncidentAIAnalysis
    ] = None


# ============================================================
# INCIDENT MODEL
# ============================================================

class Incident(BaseModel):
    """
    Main backend incident model.

    This represents the complete incident record.

    Database persistence is intentionally NOT implemented here.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique incident identifier.",
    )

    reporter_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="User who reported the incident.",
    )

    incident_type: IncidentType

    title: str

    description: str

    location: IncidentLocation

    severity: Optional[IncidentSeverity] = None

    status: IncidentStatus = (
        IncidentStatus.REPORTED
    )

    images: List[IncidentImage] = Field(
        default_factory=list,
    )

    ai_analysis: Optional[
        IncidentAIAnalysis
    ] = None

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

    resolved_at: Optional[datetime] = None


# ============================================================
# INCIDENT PUBLIC RESPONSE
# ============================================================

class IncidentPublic(BaseModel):
    """
    Safe incident representation returned to the frontend.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    reporter_id: str

    incident_type: IncidentType

    title: str

    description: str

    location: IncidentLocation

    severity: Optional[IncidentSeverity]

    status: IncidentStatus

    images: List[IncidentImage]

    ai_analysis: Optional[
        IncidentAIAnalysis
    ]

    created_at: datetime

    updated_at: datetime

    resolved_at: Optional[datetime]


# ============================================================
# INCIDENT LIST ITEM
# ============================================================

class IncidentListItem(BaseModel):
    """
    Lightweight representation for incident lists.
    """

    id: str

    incident_type: IncidentType

    title: str

    severity: Optional[IncidentSeverity]

    status: IncidentStatus

    location: IncidentLocation

    created_at: datetime


# ============================================================
# INCIDENT UPDATE MODEL
# ============================================================

class IncidentUpdate(BaseModel):
    """
    Internal model for updating an incident.

    Most fields are optional because updates are partial.
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

    description: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=5000,
    )

    severity: Optional[IncidentSeverity] = None

    status: Optional[IncidentStatus] = None

    location: Optional[IncidentLocation] = None

    ai_analysis: Optional[
        IncidentAIAnalysis
    ] = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate updated title.
        """

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Incident title cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate updated description.
        """

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Incident description cannot be empty."
            )

        return value


# ============================================================
# INCIDENT CREATION HELPER
# ============================================================

def build_incident(
    incident_id: str,
    reporter_id: str,
    incident_type: IncidentType,
    title: str,
    description: str,
    location: IncidentLocation,
    severity: Optional[IncidentSeverity] = None,
    status: IncidentStatus = IncidentStatus.REPORTED,
    images: Optional[List[IncidentImage]] = None,
    ai_analysis: Optional[
        IncidentAIAnalysis
    ] = None,
) -> Incident:
    """
    Build a complete Incident object.

    This function does not persist anything.
    """

    now = datetime.now(
        timezone.utc
    )

    return Incident(
        id=str(incident_id),
        reporter_id=str(reporter_id),
        incident_type=incident_type,
        title=title,
        description=description,
        location=location,
        severity=severity,
        status=status,
        images=images or [],
        ai_analysis=ai_analysis,
        created_at=now,
        updated_at=now,
    )


# ============================================================
# INCIDENT TO PUBLIC
# ============================================================

def incident_to_public(
    incident: Incident,
) -> IncidentPublic:
    """
    Convert Incident into a public API representation.
    """

    return IncidentPublic(
        id=incident.id,
        reporter_id=incident.reporter_id,
        incident_type=incident.incident_type,
        title=incident.title,
        description=incident.description,
        location=incident.location,
        severity=incident.severity,
        status=incident.status,
        images=incident.images,
        ai_analysis=incident.ai_analysis,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
    )


# ============================================================
# INCIDENT LIST CONVERSION
# ============================================================

def incident_to_list_item(
    incident: Incident,
) -> IncidentListItem:
    """
    Convert a complete incident into a lightweight list item.
    """

    return IncidentListItem(
        id=incident.id,
        incident_type=incident.incident_type,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        location=incident.location,
        created_at=incident.created_at,
    )


# ============================================================
# UPDATE DATA EXTRACTION
# ============================================================

def get_incident_update_data(
    update: IncidentUpdate,
) -> Dict[str, Any]:
    """
    Extract only fields supplied by the client/service.
    """

    return update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )


# ============================================================
# INCIDENT STATUS HELPERS
# ============================================================

def is_incident_active(
    incident: Incident,
) -> bool:
    """
    Determine whether an incident is still active.
    """

    return incident.status in {
        IncidentStatus.REPORTED,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.IN_PROGRESS,
    }


def is_incident_resolved(
    incident: Incident,
) -> bool:
    """
    Determine whether an incident has been resolved.
    """

    return incident.status == (
        IncidentStatus.RESOLVED
    )


def is_incident_cancelled(
    incident: Incident,
) -> bool:
    """
    Determine whether an incident has been cancelled.
    """

    return incident.status == (
        IncidentStatus.CANCELLED
    )


# ============================================================
# INCIDENT STATUS TRANSITION
# ============================================================

def apply_status_transition(
    incident: Incident,
    new_status: IncidentStatus,
) -> Incident:
    """
    Apply a status transition to an incident.

    This function updates timestamps but does not persist the
    incident.

    Service layer remains responsible for authorization and
    database persistence.
    """

    now = datetime.now(
        timezone.utc
    )

    incident.status = new_status

    incident.updated_at = now

    if new_status == IncidentStatus.RESOLVED:

        incident.resolved_at = now

    elif new_status != IncidentStatus.RESOLVED:

        incident.resolved_at = None

    return incident


# ============================================================
# INCIDENT DOCUMENT CONVERSION
# ============================================================

def incident_to_document(
    incident: Incident,
) -> Dict[str, Any]:
    """
    Convert Incident into a database-neutral dictionary.

    Member 4's database layer can transform this dictionary
    into its Firebase document structure.
    """

    return incident.model_dump(
        mode="json"
    )


# ============================================================
# INCIDENT FROM DOCUMENT
# ============================================================

def incident_from_document(
    document: Dict[str, Any],
) -> Incident:
    """
    Convert a database document into an Incident model.
    """

    if not isinstance(
        document,
        dict,
    ):
        raise ValueError(
            "Incident document must be a dictionary."
        )

    if "id" not in document:

        raise ValueError(
            "Incident document must contain an ID."
        )

    return Incident.model_validate(
        document
    )