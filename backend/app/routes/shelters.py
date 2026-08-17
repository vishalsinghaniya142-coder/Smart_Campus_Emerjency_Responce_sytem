from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from app.models.shelter import ShelterCreate, ShelterUpdate

from app.services.shelters.shelter_service import (
    create_shelter,
    delete_shelter,
    find_nearest_shelters,
    get_public_shelter,
    list_public_shelters,
    update_shelter,
)


router = APIRouter(
    prefix="/shelters",
    tags=["Shelters"],
)


# ============================================================
# CREATE SHELTER
# ============================================================

@router.post("")
async def create_shelter_endpoint(
    payload: ShelterCreate,
) -> Dict[str, Any]:

    shelter = await create_shelter(
        payload
    )

    return {
        "success": True,
        "status": "success",
        "message": "Shelter created successfully.",
        "data": shelter.model_dump(
            mode="json"
        ),
    }


# ============================================================
# GET ALL SHELTERS
# ============================================================

@router.get("")
async def get_shelters(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> Dict[str, Any]:

    shelters = await list_public_shelters(
        limit=limit,
        offset=offset,
    )

    return {
        "success": True,
        "status": "success",
        "message": "Shelters fetched successfully.",
        "data": [
            shelter.model_dump(
                mode="json"
            )
            for shelter in shelters
        ],
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# GET NEAREST SHELTERS
# ============================================================

@router.get("/nearest")
async def get_nearest_shelters(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
) -> Dict[str, Any]:

    shelters = await find_nearest_shelters(
        latitude=latitude,
        longitude=longitude,
        limit=limit,
    )

    return {
        "success": True,
        "status": "success",
        "message": "Nearest shelters fetched successfully.",
        "data": [
            shelter.model_dump(
                mode="json"
            )
            for shelter in shelters
        ],
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

    if not shelter_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Shelter ID is required.",
        )

    shelter = await get_public_shelter(
        shelter_id
    )

    if shelter is None:
        raise HTTPException(
            status_code=404,
            detail="Shelter not found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Shelter fetched successfully.",
        "data": shelter.model_dump(
            mode="json"
        ),
    }


# ============================================================
# UPDATE SHELTER
# ============================================================

@router.patch("/{shelter_id}")
async def update_shelter_endpoint(
    shelter_id: str,
    payload: ShelterUpdate,
) -> Dict[str, Any]:

    shelter = await update_shelter(
        shelter_id=shelter_id,
        payload=payload,
    )

    if shelter is None:
        raise HTTPException(
            status_code=404,
            detail="Shelter not found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Shelter updated successfully.",
        "data": shelter.model_dump(
            mode="json"
        ),
    }


# ============================================================
# DELETE SHELTER
# ============================================================

@router.delete("/{shelter_id}")
async def delete_shelter_endpoint(
    shelter_id: str,
) -> Dict[str, Any]:

    deleted = await delete_shelter(
        shelter_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Shelter not found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Shelter deleted successfully.",
        "data": {
            "shelter_id": shelter_id,
        },
    }