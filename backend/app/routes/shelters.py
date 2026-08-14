from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/shelters",
    tags=["Shelters"],
)


# ============================================================
# GET ALL SHELTERS
# ============================================================

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
        "message": "Shelter endpoint is ready.",
        "data": [],
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

    return {
        "success": True,
        "message": "Nearest shelter endpoint is ready.",
        "data": [],
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

    return {
        "success": True,
        "message": "Shelter lookup endpoint is ready.",
        "data": None,
        "shelter_id": shelter_id,
    }