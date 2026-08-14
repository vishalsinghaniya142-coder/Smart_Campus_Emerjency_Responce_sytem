from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.shelter import (
    Shelter,
    ShelterAmenities,
    ShelterCapacity,
    ShelterLocation,
    ShelterStatus,
    ShelterType,
)


# ============================================================
# LOCATION
# ============================================================

class ShelterLocationRequest(BaseModel):
    """
    Location data required for a shelter.
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
# CAPACITY
# ============================================================

class ShelterCapacityRequest(BaseModel):
    """
    Shelter capacity information.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    total: int = Field(
        default=0,
        ge=0,
    )

    occupied: int = Field(
        default=0,
        ge=0,
    )

    available: Optional[int] = Field(
        default=None,
        ge=0,
    )


# ============================================================
# AMENITIES
# ============================================================

class ShelterAmenitiesRequest(BaseModel):
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
# CREATE SHELTER REQUEST
# ============================================================

class ShelterCreateRequest(BaseModel):
    """
    Request body for creating a shelter.

    Endpoint:
        POST /shelters

    created_by is intentionally not accepted from the client.
    It should come from authenticated backend context.
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

    location: ShelterLocationRequest

    capacity: ShelterCapacityRequest = Field(
        default_factory=ShelterCapacityRequest,
    )

    amenities: ShelterAmenitiesRequest = Field(
        default_factory=ShelterAmenitiesRequest,
    )

    status: ShelterStatus = (
        ShelterStatus.AVAILABLE
    )

    contact_number: Optional[str] = Field(
        default=None,
        max_length=30,
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
# UPDATE SHELTER REQUEST
# ============================================================

class ShelterUpdateRequest(BaseModel):
    """
    Partial shelter update request.
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
        ShelterLocationRequest
    ] = None

    capacity: Optional[
        ShelterCapacityRequest
    ] = None

    amenities: Optional[
        ShelterAmenitiesRequest
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
# SHELTER RESPONSE
# ============================================================

class ShelterResponse(BaseModel):
    """
    Complete shelter API response.
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

class ShelterListItemResponse(BaseModel):
    """
    Lightweight shelter response for listing.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str

    name: str

    shelter_type: ShelterType

    location: ShelterLocation

    status: ShelterStatus

    available_capacity: int

    created_at: datetime


# ============================================================
# SHELTER LIST RESPONSE
# ============================================================

class ShelterListResponse(BaseModel):
    """
    Response for:

        GET /shelters
    """

    shelters: List[
        ShelterListItemResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# SHELTER DETAIL RESPONSE
# ============================================================

class ShelterDetailResponse(BaseModel):
    """
    Detailed shelter response wrapper.
    """

    shelter: ShelterResponse


# ============================================================
# SHELTER CREATE RESPONSE
# ============================================================

class ShelterCreateResponse(BaseModel):
    """
    Response after shelter creation.
    """

    shelter: ShelterResponse


# ============================================================
# SHELTER SEARCH REQUEST
# ============================================================

class ShelterSearchRequest(BaseModel):
    """
    Request contract for shelter search.

    This only validates API input.

    Location/route calculations are not implemented here.
    """

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

    radius_meters: int = Field(
        default=5000,
        ge=100,
        le=100000,
    )

    shelter_type: Optional[
        ShelterType
    ] = None

    available_only: bool = True


# ============================================================
# SHELTER SEARCH RESULT
# ============================================================

class ShelterSearchResultResponse(BaseModel):
    """
    Response item for nearby shelter search.
    """

    shelter: ShelterResponse

    distance_meters: Optional[float] = Field(
        default=None,
        ge=0,
    )

    estimated_minutes: Optional[float] = Field(
        default=None,
        ge=0,
    )


class ShelterSearchResponse(BaseModel):
    """
    Complete nearby shelter search response.
    """

    shelters: List[
        ShelterSearchResultResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# CAPACITY UPDATE REQUEST
# ============================================================

class ShelterCapacityUpdateRequest(BaseModel):
    """
    Request to update shelter occupancy.
    """

    occupied: int = Field(
        ...,
        ge=0,
    )


# ============================================================
# CAPACITY RESPONSE
# ============================================================

class ShelterCapacityResponse(BaseModel):
    """
    Current shelter capacity response.
    """

    shelter_id: str

    total: int

    occupied: int

    available: int

    status: ShelterStatus


# ============================================================
# CONVERSION HELPERS
# ============================================================

def location_request_to_model(
    location: ShelterLocationRequest,
) -> ShelterLocation:
    """
    Convert request location into domain model.
    """

    return ShelterLocation(
        latitude=location.latitude,
        longitude=location.longitude,
        address=location.address,
        building=location.building,
        floor=location.floor,
        room=location.room,
    )


def capacity_request_to_model(
    capacity: ShelterCapacityRequest,
) -> ShelterCapacity:
    """
    Convert request capacity into domain model.
    """

    available = capacity.available

    if available is None:
        available = max(
            capacity.total
            - capacity.occupied,
            0,
        )

    return ShelterCapacity(
        total=capacity.total,
        occupied=capacity.occupied,
        available=available,
    )


def amenities_request_to_model(
    amenities: ShelterAmenitiesRequest,
) -> ShelterAmenities:
    """
    Convert request amenities into domain model.
    """

    return ShelterAmenities(
        drinking_water=amenities.drinking_water,
        food=amenities.food,
        electricity=amenities.electricity,
        washroom=amenities.washroom,
        first_aid=amenities.first_aid,
        wheelchair_accessible=(
            amenities.wheelchair_accessible
        ),
        security_available=(
            amenities.security_available
        ),
        medical_support=(
            amenities.medical_support
        ),
    )


# ============================================================
# CREATE REQUEST CONVERSION
# ============================================================

def create_request_to_model_data(
    payload: ShelterCreateRequest,
    created_by: Optional[str] = None,
) -> dict:
    """
    Convert API request into service-layer data.

    created_by is supplied by backend authentication.
    """

    return {
        "name": payload.name,
        "shelter_type": payload.shelter_type,
        "description": payload.description,
        "location": location_request_to_model(
            payload.location
        ),
        "capacity": capacity_request_to_model(
            payload.capacity
        ),
        "amenities": amenities_request_to_model(
            payload.amenities
        ),
        "status": payload.status,
        "contact_number": payload.contact_number,
        "created_by": created_by,
    }


# ============================================================
# UPDATE REQUEST CONVERSION
# ============================================================

def update_request_to_model_data(
    payload: ShelterUpdateRequest,
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
            ShelterLocationRequest,
        ):
            data["location"] = (
                location_request_to_model(
                    location
                )
            )

    if "capacity" in data:

        capacity = data["capacity"]

        if isinstance(
            capacity,
            ShelterCapacityRequest,
        ):
            data["capacity"] = (
                capacity_request_to_model(
                    capacity
                )
            )

    if "amenities" in data:

        amenities = data["amenities"]

        if isinstance(
            amenities,
            ShelterAmenitiesRequest,
        ):
            data["amenities"] = (
                amenities_request_to_model(
                    amenities
                )
            )

    return data


# ============================================================
# RESPONSE BUILDERS
# ============================================================

def build_shelter_response(
    shelter: Shelter,
) -> ShelterResponse:
    """
    Convert domain model to API response.
    """

    return ShelterResponse.model_validate(
        shelter
    )


def build_shelter_detail_response(
    shelter: Shelter,
) -> ShelterDetailResponse:
    """
    Build detailed shelter response.
    """

    return ShelterDetailResponse(
        shelter=build_shelter_response(
            shelter
        )
    )


def build_shelter_create_response(
    shelter: Shelter,
) -> ShelterCreateResponse:
    """
    Build create response.
    """

    return ShelterCreateResponse(
        shelter=build_shelter_response(
            shelter
        )
    )


def build_shelter_list_response(
    shelters: List[Shelter],
) -> ShelterListResponse:
    """
    Build shelter list response.
    """

    items = []

    for shelter in shelters:

        available_capacity = max(
            shelter.capacity.total
            - shelter.capacity.occupied,
            0,
        )

        items.append(
            ShelterListItemResponse(
                id=shelter.id,
                name=shelter.name,
                shelter_type=shelter.shelter_type,
                location=shelter.location,
                status=shelter.status,
                available_capacity=(
                    available_capacity
                ),
                created_at=shelter.created_at,
            )
        )

    return ShelterListResponse(
        shelters=items,
        total=len(items),
    )


# ============================================================
# SEARCH RESPONSE BUILDER
# ============================================================

def build_shelter_search_response(
    results: list,
) -> ShelterSearchResponse:
    """
    Build nearby shelter search response.
    """

    response_items = []

    for result in results:

        if isinstance(
            result,
            ShelterSearchResultResponse,
        ):
            response_items.append(
                result
            )
            continue

        shelter = result.get(
            "shelter"
        )

        response_items.append(
            ShelterSearchResultResponse(
                shelter=build_shelter_response(
                    shelter
                ),
                distance_meters=result.get(
                    "distance_meters"
                ),
                estimated_minutes=result.get(
                    "estimated_minutes"
                ),
            )
        )

    return ShelterSearchResponse(
        shelters=response_items,
        total=len(response_items),
    )


# ============================================================
# CAPACITY RESPONSE BUILDER
# ============================================================

def build_capacity_response(
    shelter: Shelter,
) -> ShelterCapacityResponse:
    """
    Build current shelter capacity response.
    """

    available = max(
        shelter.capacity.total
        - shelter.capacity.occupied,
        0,
    )

    return ShelterCapacityResponse(
        shelter_id=shelter.id,
        total=shelter.capacity.total,
        occupied=shelter.capacity.occupied,
        available=available,
        status=shelter.status,
    )


# ============================================================
# EMPTY UPDATE CHECK
# ============================================================

def has_shelter_updates(
    payload: ShelterUpdateRequest,
) -> bool:
    """
    Check whether an update request contains any fields.
    """

    return bool(
        payload.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )
    )