from enum import Enum
from typing import Any, Dict, List, Optional

from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# SHELTER ENUMS
# ============================================================

class ShelterType(str, Enum):
    """
    Type of emergency support location.
    """

    SHELTER = "shelter"
    MEDICAL_CENTER = "medical_center"
    SAFE_ZONE = "safe_zone"
    ASSEMBLY_POINT = "assembly_point"


class ShelterStatus(str, Enum):
    """
    Current operational status of a shelter.
    """

    AVAILABLE = "available"
    LIMITED = "limited"
    FULL = "full"
    CLOSED = "closed"


# ============================================================
# SHELTER LOCATION
# ============================================================

class ShelterLocation(BaseModel):
    """
    Geographic information for a shelter.

    IMPORTANT:

    This model only stores location data.

    Actual Maps / route / geocoding logic belongs to Member 4's
    services/maps/ layer.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Shelter latitude.",
        examples=[26.8467],
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Shelter longitude.",
        examples=[80.9462],
    )

    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable shelter address.",
    )

    building: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Building name.",
    )

    floor: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Floor information.",
    )

    room: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Room or specific area.",
    )


# ============================================================
# SHELTER CAPACITY
# ============================================================

class ShelterCapacity(BaseModel):
    """
    Capacity information for a shelter.

    The values can later be updated using Firebase/database
    integration.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
        description="Total available capacity.",
    )

    occupied: int = Field(
        default=0,
        ge=0,
        description="Currently occupied capacity.",
    )

    available: int = Field(
        default=0,
        ge=0,
        description="Currently available capacity.",
    )

    @field_validator("occupied")
    @classmethod
    def validate_occupied(
        cls,
        value: int,
    ) -> int:

        if value < 0:
            raise ValueError(
                "Occupied capacity cannot be negative."
            )

        return value

    def calculate_available(self) -> int:
        """
        Calculate available capacity from total and occupied.
        """

        return max(
            self.total - self.occupied,
            0,
        )


# ============================================================
# SHELTER AMENITIES
# ============================================================

class ShelterAmenities(BaseModel):
    """
    Facilities available at the shelter.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    drinking_water: bool = False

    food: bool = False

    electricity: bool = False

    washroom: bool = False

    first_aid: bool = False

    wheelchair_accessible: bool = False

    security_available: bool = False

    medical_support: bool = False


# ============================================================
# SHELTER BASE
# ============================================================

class ShelterBase(BaseModel):
    """
    Common shelter fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Shelter name.",
        examples=["Main Auditorium Safe Shelter"],
    )

    shelter_type: ShelterType = Field(
        default=ShelterType.SHELTER,
        description="Type of emergency facility.",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Shelter description.",
    )

    location: ShelterLocation

    capacity: ShelterCapacity = Field(
        default_factory=ShelterCapacity,
    )

    amenities: ShelterAmenities = Field(
        default_factory=ShelterAmenities,
    )

    status: ShelterStatus = Field(
        default=ShelterStatus.AVAILABLE,
    )

    contact_number: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Emergency contact number.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Shelter name cannot be empty."
            )

        return value


# ============================================================
# SHELTER CREATE
# ============================================================

class ShelterCreate(BaseModel):
    """
    Internal model used to create a shelter record.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    shelter_type: ShelterType = (
        ShelterType.SHELTER
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    location: ShelterLocation

    capacity: ShelterCapacity = Field(
        default_factory=ShelterCapacity,
    )

    amenities: ShelterAmenities = Field(
        default_factory=ShelterAmenities,
    )

    status: ShelterStatus = (
        ShelterStatus.AVAILABLE
    )

    contact_number: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    created_by: Optional[str] = Field(
        default=None,
        max_length=200,
    )


# ============================================================
# SHELTER MODEL
# ============================================================

class Shelter(BaseModel):
    """
    Complete shelter domain model.

    Database persistence is intentionally NOT implemented here.

    Member 4's Firebase/database layer will persist this data.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique shelter identifier.",
    )

    name: str

    shelter_type: ShelterType

    description: Optional[str] = None

    location: ShelterLocation

    capacity: ShelterCapacity

    amenities: ShelterAmenities

    status: ShelterStatus

    contact_number: Optional[str] = None

    created_by: Optional[str] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


# ============================================================
# PUBLIC SHELTER RESPONSE
# ============================================================

class ShelterPublic(BaseModel):
    """
    Safe shelter representation for frontend/API responses.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    name: str

    shelter_type: ShelterType

    description: Optional[str]

    location: ShelterLocation

    capacity: ShelterCapacity

    amenities: ShelterAmenities

    status: ShelterStatus

    contact_number: Optional[str]

    created_at: datetime

    updated_at: datetime


# ============================================================
# SHELTER LIST ITEM
# ============================================================

class ShelterListItem(BaseModel):
    """
    Lightweight representation for shelter lists.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: str

    name: str

    shelter_type: ShelterType

    location: ShelterLocation

    status: ShelterStatus

    available_capacity: int

    created_at: datetime


# ============================================================
# SHELTER UPDATE
# ============================================================

class ShelterUpdate(BaseModel):
    """
    Partial update model for shelter information.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    shelter_type: Optional[
        ShelterType
    ] = None

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    location: Optional[
        ShelterLocation
    ] = None

    capacity: Optional[
        ShelterCapacity
    ] = None

    amenities: Optional[
        ShelterAmenities
    ] = None

    status: Optional[
        ShelterStatus
    ] = None

    contact_number: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Shelter name cannot be empty."
            )

        return value


# ============================================================
# SHELTER SEARCH RESULT
# ============================================================

class ShelterSearchResult(BaseModel):
    """
    Represents a shelter returned by a nearby-shelter search.

    Distance is calculated by the Maps/location layer, not by
    this model.
    """

    shelter: ShelterPublic

    distance_meters: Optional[float] = Field(
        default=None,
        ge=0,
        description="Distance from requested location.",
    )

    estimated_minutes: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated travel time.",
    )


# ============================================================
# SHELTER DOCUMENT CONVERSION
# ============================================================

def shelter_to_document(
    shelter: Shelter,
) -> Dict[str, Any]:
    """
    Convert shelter model into a database-neutral dictionary.

    Member 4 can use this structure in the Firebase layer.
    """

    return shelter.model_dump(
        mode="json"
    )


# ============================================================
# SHELTER FROM DOCUMENT
# ============================================================

def shelter_from_document(
    document: Dict[str, Any],
) -> Shelter:
    """
    Convert a Firebase/database document into Shelter model.
    """

    if not isinstance(
        document,
        dict,
    ):
        raise ValueError(
            "Shelter document must be a dictionary."
        )

    if "id" not in document:

        raise ValueError(
            "Shelter document must contain an ID."
        )

    return Shelter.model_validate(
        document
    )


# ============================================================
# BUILD SHELTER
# ============================================================

def build_shelter(
    shelter_id: str,
    name: str,
    location: ShelterLocation,
    shelter_type: ShelterType = ShelterType.SHELTER,
    description: Optional[str] = None,
    capacity: Optional[
        ShelterCapacity
    ] = None,
    amenities: Optional[
        ShelterAmenities
    ] = None,
    status: ShelterStatus = (
        ShelterStatus.AVAILABLE
    ),
    contact_number: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Shelter:
    """
    Build a complete Shelter object.

    No database operation occurs here.
    """

    now = datetime.now(
        timezone.utc
    )

    return Shelter(
        id=str(shelter_id),
        name=name,
        shelter_type=shelter_type,
        description=description,
        location=location,
        capacity=(
            capacity
            or ShelterCapacity()
        ),
        amenities=(
            amenities
            or ShelterAmenities()
        ),
        status=status,
        contact_number=contact_number,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )


# ============================================================
# AVAILABLE CAPACITY
# ============================================================

def get_available_capacity(
    shelter: Shelter,
) -> int:
    """
    Return currently available shelter capacity.
    """

    return max(
        shelter.capacity.total
        - shelter.capacity.occupied,
        0,
    )


# ============================================================
# SHELTER AVAILABILITY
# ============================================================

def is_shelter_available(
    shelter: Shelter,
) -> bool:
    """
    Determine whether the shelter can currently accept
    people.
    """

    if shelter.status == ShelterStatus.CLOSED:
        return False

    if shelter.status == ShelterStatus.FULL:
        return False

    return (
        get_available_capacity(
            shelter
        )
        > 0
    )


# ============================================================
# UPDATE CAPACITY
# ============================================================

def update_shelter_occupancy(
    shelter: Shelter,
    occupied: int,
) -> Shelter:
    """
    Update occupancy information.

    This only changes the in-memory model.

    Persistence belongs to the service/database layer.
    """

    if occupied < 0:

        raise ValueError(
            "Occupied capacity cannot be negative."
        )

    if occupied > shelter.capacity.total:

        raise ValueError(
            "Occupied capacity cannot exceed total capacity."
        )

    shelter.capacity.occupied = occupied

    shelter.capacity.available = max(
        shelter.capacity.total
        - occupied,
        0,
    )

    if occupied >= shelter.capacity.total:

        shelter.status = (
            ShelterStatus.FULL
        )

    elif occupied > 0:

        shelter.status = (
            ShelterStatus.LIMITED
        )

    else:

        shelter.status = (
            ShelterStatus.AVAILABLE
        )

    shelter.updated_at = datetime.now(
        timezone.utc
    )

    return shelter


# ============================================================
# SHELTER PUBLIC DATA
# ============================================================

def shelter_to_public(
    shelter: Shelter,
) -> ShelterPublic:
    """
    Convert complete shelter model into public representation.
    """

    return ShelterPublic(
        id=shelter.id,
        name=shelter.name,
        shelter_type=shelter.shelter_type,
        description=shelter.description,
        location=shelter.location,
        capacity=shelter.capacity,
        amenities=shelter.amenities,
        status=shelter.status,
        contact_number=shelter.contact_number,
        created_at=shelter.created_at,
        updated_at=shelter.updated_at,
    )


# ============================================================
# SHELTER LIST ITEM
# ============================================================

def shelter_to_list_item(
    shelter: Shelter,
) -> ShelterListItem:
    """
    Convert shelter into lightweight list representation.
    """

    return ShelterListItem(
        id=shelter.id,
        name=shelter.name,
        shelter_type=shelter.shelter_type,
        location=shelter.location,
        status=shelter.status,
        available_capacity=(
            get_available_capacity(
                shelter
            )
        ),
        created_at=shelter.created_at,
    )


# ============================================================
# SHELTER SEARCH RESULT BUILDER
# ============================================================

def build_shelter_search_result(
    shelter: Shelter,
    distance_meters: Optional[float] = None,
    estimated_minutes: Optional[float] = None,
) -> ShelterSearchResult:
    """
    Build a nearby-shelter search result.

    Distance/travel time comes from Member 4's Maps layer.
    """

    return ShelterSearchResult(
        shelter=shelter_to_public(
            shelter
        ),
        distance_meters=distance_meters,
        estimated_minutes=estimated_minutes,
    )