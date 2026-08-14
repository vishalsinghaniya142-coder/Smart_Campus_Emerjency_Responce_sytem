from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.incident import (
    IncidentImage,
    IncidentLocation,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)


# ============================================================
# INCIDENT LOCATION REQUEST
# ============================================================

class IncidentLocationRequest(BaseModel):
    """
    Location information supplied while reporting an incident.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude of the incident location.",
        examples=[26.8467],
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude of the incident location.",
        examples=[80.9462],
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable address.",
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
# INCIDENT IMAGE REQUEST
# ============================================================

class IncidentImageRequest(BaseModel):
    """
    Metadata for an incident image.

    The actual file upload is handled by the route when
    multipart/form-data is required.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    url: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    storage_path: Optional[str] = Field(
        default=None,
        max_length=1000,
    )

    filename: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    content_type: Optional[str] = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# CREATE INCIDENT REQUEST
# ============================================================

class IncidentCreateRequest(BaseModel):
    """
    Request body for:

        POST /incidents

    Example:

        {
            "incident_type": "fire",
            "title": "Fire near laboratory",
            "description": "Smoke is visible near the lab.",
            "location": {
                "latitude": 26.8467,
                "longitude": 80.9462,
                "building": "Academic Block",
                "floor": "2nd Floor",
                "room": "Room 204"
            }
        }

    reporter_id is NOT accepted from the frontend.

    It must come from the authenticated JWT user.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    incident_type: IncidentType = Field(
        ...,
        description="Type of emergency.",
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
        description="Detailed description of the incident.",
    )

    location: IncidentLocationRequest

    severity: Optional[IncidentSeverity] = Field(
        default=None,
        description="Known severity, if available.",
    )

    images: List[IncidentImageRequest] = Field(
        default_factory=list,
        description="Optional image metadata.",
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
# INCIDENT UPDATE REQUEST
# ============================================================

class IncidentUpdateRequest(BaseModel):
    """
    Request body for updating an existing incident.

    This is a PATCH-style schema, therefore every field is
    optional.
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

    location: Optional[IncidentLocationRequest] = None

    images: Optional[
        List[IncidentImageRequest]
    ] = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate optional title.
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
        Validate optional description.
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
# INCIDENT RESPONSE
# ============================================================

class IncidentResponse(BaseModel):
    """
    Complete public incident response.

    Used for:
        - incident creation result
        - incident detail
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
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

    ai_analysis: Optional[dict] = None

    created_at: datetime

    updated_at: datetime

    resolved_at: Optional[datetime] = None


# ============================================================
# INCIDENT LIST ITEM RESPONSE
# ============================================================

class IncidentListItemResponse(BaseModel):
    """
    Lightweight incident representation used in list APIs.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    incident_type: IncidentType

    title: str

    severity: Optional[IncidentSeverity]

    status: IncidentStatus

    location: IncidentLocation

    created_at: datetime


# ============================================================
# INCIDENT LIST RESPONSE
# ============================================================

class IncidentListResponse(BaseModel):
    """
    Response contract for:

        GET /incidents
    """

    incidents: List[
        IncidentListItemResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# INCIDENT DETAIL RESPONSE
# ============================================================

class IncidentDetailResponse(BaseModel):
    """
    Response contract for:

        GET /incidents/{incident_id}
    """

    incident: IncidentResponse


# ============================================================
# INCIDENT CREATE RESPONSE
# ============================================================

class IncidentCreateResponse(BaseModel):
    """
    Response contract for:

        POST /incidents
    """

    incident: IncidentResponse


# ============================================================
# INCIDENT STATUS RESPONSE
# ============================================================

class IncidentStatusResponse(BaseModel):
    """
    Lightweight incident status response.
    """

    id: str

    status: IncidentStatus

    severity: Optional[IncidentSeverity]

    updated_at: datetime


# ============================================================
# INCIDENT FILTER REQUEST
# ============================================================

class IncidentFilterRequest(BaseModel):
    """
    Internal filter contract for incident listing.

    These values can later be populated from query parameters
    in routes/incidents.py.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    incident_type: Optional[
        IncidentType
    ] = None

    severity: Optional[
        IncidentSeverity
    ] = None

    status: Optional[
        IncidentStatus
    ] = None

    reporter_id: Optional[str] = Field(
        default=None,
        max_length=200,
    )

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
# CONVERSION: REQUEST LOCATION -> MODEL LOCATION
# ============================================================

def location_request_to_model(
    location: IncidentLocationRequest,
) -> IncidentLocation:
    """
    Convert API location schema into the incident domain model.
    """

    return IncidentLocation(
        latitude=location.latitude,
        longitude=location.longitude,
        address=location.address,
        building=location.building,
        floor=location.floor,
        room=location.room,
    )


# ============================================================
# CONVERSION: IMAGE REQUEST -> MODEL IMAGE
# ============================================================

def image_request_to_model(
    image: IncidentImageRequest,
) -> IncidentImage:
    """
    Convert image request metadata into the incident model.
    """

    return IncidentImage(
        url=image.url,
        storage_path=image.storage_path,
        filename=image.filename,
        content_type=image.content_type,
    )


# ============================================================
# CONVERSION: CREATE REQUEST -> MODEL DATA
# ============================================================

def create_request_to_model_data(
    payload: IncidentCreateRequest,
    reporter_id: str,
) -> dict:
    """
    Convert the API request into data expected by the incident
    service/model layer.

    reporter_id comes from authentication and NOT from the
    client request.
    """

    if not reporter_id:
        raise ValueError(
            "Authenticated reporter ID is required."
        )

    return {
        "reporter_id": reporter_id,
        "incident_type": payload.incident_type,
        "title": payload.title,
        "description": payload.description,
        "location": location_request_to_model(
            payload.location
        ),
        "severity": payload.severity,
        "images": [
            image_request_to_model(
                image
            )
            for image in payload.images
        ],
    }


# ============================================================
# CONVERSION: UPDATE REQUEST -> MODEL DATA
# ============================================================

def update_request_to_model_data(
    payload: IncidentUpdateRequest,
) -> dict:
    """
    Convert only supplied update fields into service-layer
    data.
    """

    data = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "location" in data:

        location = data["location"]

        if isinstance(
            location,
            IncidentLocationRequest,
        ):

            data["location"] = (
                location_request_to_model(
                    location
                )
            )

    if "images" in data:

        images = data["images"]

        data["images"] = [
            image_request_to_model(
                image
            )
            for image in images
        ]

    return data


# ============================================================
# RESPONSE CONVERTER
# ============================================================

def build_incident_response(
    incident: object,
) -> IncidentResponse:
    """
    Convert an Incident model/object into the public API
    response schema.
    """

    return IncidentResponse.model_validate(
        incident
    )


# ============================================================
# LIST ITEM CONVERTER
# ============================================================

def build_incident_list_item(
    incident: object,
) -> IncidentListItemResponse:
    """
    Convert an incident into a lightweight list response.
    """

    return IncidentListItemResponse.model_validate(
        incident
    )


# ============================================================
# BUILD LIST RESPONSE
# ============================================================

def build_incident_list_response(
    incidents: List[object],
) -> IncidentListResponse:
    """
    Build the response for GET /incidents.
    """

    items = [
        build_incident_list_item(
            incident
        )
        for incident in incidents
    ]

    return IncidentListResponse(
        incidents=items,
        total=len(items),
    )