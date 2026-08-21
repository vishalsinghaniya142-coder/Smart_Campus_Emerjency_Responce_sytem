from math import atan2, cos, radians, sin, sqrt
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_current_user
from app.models.shelter import ShelterCreate
from app.schemas.shelter_schema import ShelterUpdateRequest
from app.utils.response import created_response
from app.services.database.firebase_client import db

router = APIRouter(
    tags=["Shelters"],
)


SHELTERS_COLLECTION = "shelters"


def shelter_for_map(document: Any) -> Dict[str, Any]:
    data = document.to_dict() or {}
    location = data.get("location") or {}
    capacity = data.get("capacity") or {}

    if not isinstance(location, dict):
        location = {"address": str(location)}
    if not isinstance(capacity, dict):
        capacity = {"occupied": 0, "total": capacity}

    return {
        "id": document.id,
        "name": data.get("name", "Emergency shelter"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "address": location.get("address"),
        "capacity": f"{capacity.get('occupied', 0)} / {capacity.get('total', 0)}",
        "availability": data.get("status", "available").replace("_", " ").title(),
        "description": data.get("description"),
        "amenities": data.get("amenities", {}),
    }


def load_shelters() -> List[Dict[str, Any]]:
    return [
        shelter_for_map(document)
        for document in db.collection(SHELTERS_COLLECTION).stream()
    ]


def normalize_firestore_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: normalize_firestore_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_firestore_value(item) for item in value]
    return value


def distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_km = 6371
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return round(earth_radius_km * 2 * atan2(sqrt(value), sqrt(1 - value)), 2)


# ============================================================
# GET ALL SHELTERS
# ============================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_shelter(
    payload: ShelterCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user.get("user_id") or current_user.get("id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user could not be identified.")

    shelter_id = f"shelter_{uuid4().hex}"
    now = datetime.now(timezone.utc)
    data = payload.model_dump(mode="python")
    data["created_by"] = user_id
    data["created_at"] = now
    data["updated_at"] = now
    data = normalize_firestore_value(data)

    document_ref = db.collection(SHELTERS_COLLECTION).document(shelter_id)
    document_ref.set({"id": shelter_id, **data})
    return created_response(
        data=shelter_for_map(document_ref.get()),
        message="Shelter created successfully.",
    )


@router.patch("/{shelter_id}")
async def update_shelter(
    shelter_id: str,
    payload: ShelterUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user.get("user_id") or current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user could not be identified.")

    document_ref = db.collection(SHELTERS_COLLECTION).document(shelter_id)
    document = document_ref.get()
    if not document.exists:
        raise HTTPException(status_code=404, detail="Shelter not found.")

    updates = payload.model_dump(exclude_unset=True, exclude_none=True, mode="json")
    if not updates:
        raise HTTPException(status_code=400, detail="No shelter fields were provided.")

    updates["updated_at"] = datetime.now(timezone.utc)
    document_ref.update(normalize_firestore_value(updates))
    updated_document = document_ref.get()
    return {
        "success": True,
        "message": "Shelter updated successfully.",
        "data": shelter_for_map(updated_document),
    }

@router.get("")
async def get_shelters(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """
    Get shelters.

    Member 2:
        Exposes the API endpoint only.

    Member 4 later:
        Will connect Firebase / shelter service here.
    """

    return {
        "success": True,
        "message": "Shelters retrieved successfully.",
        "data": load_shelters()[offset:offset + limit],
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# GET NEAREST SHELTERS
# ============================================================

@router.get("/nearest")
async def get_nearest_shelters(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    limit: int = Query(default=5, ge=1, le=20),
) -> Dict[str, Any]:
    """
    Get nearest shelters.

    Member 2:
        API contract only.

    Member 4 later:
        Will connect Maps/Firebase and implement
        actual nearest-shelter calculation.
    """

    shelters = []
    for shelter in load_shelters():
        if shelter["latitude"] is None or shelter["longitude"] is None:
            continue
        shelters.append(
            {
                **shelter,
                "distance_km": distance_km(
                    latitude,
                    longitude,
                    shelter["latitude"],
                    shelter["longitude"],
                ),
            }
        )
    shelters.sort(key=lambda shelter: shelter["distance_km"])

    return {
        "success": True,
        "message": "Nearest shelters retrieved successfully.",
        "data": shelters[:limit],
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "limit": limit,
    }


# ============================================================
# GET SHELTER BY ID
# ============================================================

@router.get("/{shelter_id}")
async def get_shelter(
    shelter_id: str,
) -> Dict[str, Any]:
    """
    Get a shelter by ID.

    Actual database lookup will be connected later.
    """

    if not shelter_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Shelter ID is required.",
        )

    document = db.collection(SHELTERS_COLLECTION).document(shelter_id).get()

    if not document.exists:
        raise HTTPException(
            status_code=404,
            detail="Shelter not found.",
        )

    return {
        "success": True,
        "message": "Shelter retrieved successfully.",
        "data": shelter_for_map(document),
        "shelter_id": shelter_id,
    }


@router.delete("/{shelter_id}")
async def delete_shelter(
    shelter_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user.get("user_id") or current_user.get("id") or current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user could not be identified.")

    document_ref = db.collection(SHELTERS_COLLECTION).document(shelter_id)
    if not document_ref.get().exists:
        raise HTTPException(status_code=404, detail="Shelter not found.")

    document_ref.delete()
    return {
        "success": True,
        "message": "Shelter deleted successfully.",
        "shelter_id": shelter_id,
    }