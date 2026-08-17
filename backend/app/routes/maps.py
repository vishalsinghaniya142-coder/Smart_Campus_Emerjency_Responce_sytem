from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, status

from app.services.maps.map_service import (
    search_location,
    get_location_coordinates,
    find_route,
    find_safe_route,
)


router = APIRouter()


# ============================================================
# GEOCODE ADDRESS
# ============================================================

@router.get(
    "/geocode",
    status_code=status.HTTP_200_OK,
)
async def geocode_location(
    address: str = Query(
        ...,
        min_length=1,
    ),
) -> Dict[str, Any]:

    result = search_location(address)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location could not be found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Location geocoded successfully.",
        "data": result,
    }


# ============================================================
# GET COORDINATES
# ============================================================

@router.get(
    "/coordinates",
    status_code=status.HTTP_200_OK,
)
async def get_coordinates_endpoint(
    address: str = Query(
        ...,
        min_length=1,
    ),
) -> Dict[str, Any]:

    result = get_location_coordinates(address)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location coordinates could not be found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Location coordinates fetched successfully.",
        "data": result,
    }


# ============================================================
# NORMAL ROUTE
# ============================================================

@router.get(
    "/route",
    status_code=status.HTTP_200_OK,
)
async def get_route_endpoint(
    start_latitude: float = Query(..., ge=-90, le=90),
    start_longitude: float = Query(..., ge=-180, le=180),
    end_latitude: float = Query(..., ge=-90, le=90),
    end_longitude: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:

    result = find_route(
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route could not be found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Route fetched successfully.",
        "data": result,
    }


# ============================================================
# SAFE ROUTE
# ============================================================

@router.get(
    "/safe-route",
    status_code=status.HTTP_200_OK,
)
async def get_safe_route_endpoint(
    start_latitude: float = Query(..., ge=-90, le=90),
    start_longitude: float = Query(..., ge=-180, le=180),
    end_latitude: float = Query(..., ge=-90, le=90),
    end_longitude: float = Query(..., ge=-180, le=180),
) -> Dict[str, Any]:

    result = find_safe_route(
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safe route could not be found.",
        )

    return {
        "success": True,
        "status": "success",
        "message": "Safe route fetched successfully.",
        "data": result,
    }