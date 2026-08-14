from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas.sos_schema import (
    SOSCreateRequest,
    SOSCreateResponse,
    SOSUpdateRequest,
    SOSStatusResponse,
)
from app.services.sos_service import (
    create_sos,
    get_sos,
    update_sos,
)


router = APIRouter(
    prefix="/sos",
    tags=["SOS"],
)


# ============================================================
# HELPER — AUTHENTICATED USER ID
# ============================================================

def get_authenticated_user_id(
    current_user: Dict[str, Any],
) -> str:
    """
    Extract authenticated user ID from the dictionary returned
    by get_current_user().
    """

    if not isinstance(
        current_user,
        dict,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication context.",
        )

    user_id = (
        current_user.get("user_id")
        or current_user.get("id")
        or current_user.get("sub")
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID not found.",
        )

    return str(user_id)


# ============================================================
# CREATE SOS
# ============================================================

@router.post(
    "",
    response_model=SOSCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sos_request(
    payload: SOSCreateRequest,
    current_user: Dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Create a new emergency SOS.

    Required API:

        POST /sos

    The user ID is taken from authentication context.
    It is never accepted from the request body.
    """

    user_id = get_authenticated_user_id(
        current_user
    )

    try:
        sos = await create_sos(
            payload=payload,
            user_id=user_id,
        )

        return SOSCreateResponse(
            sos=sos
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        # Database/Firebase is not connected yet.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# ============================================================
# GET SOS BY ID
# ============================================================

@router.get(
    "/{sos_id}",
    status_code=status.HTTP_200_OK,
)
async def get_sos_request(
    sos_id: str,
    current_user: Dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Get an SOS request by ID.
    """

    user_id = get_authenticated_user_id(
        current_user
    )

    try:

        sos = await get_sos(
            sos_id
        )

        if sos is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOS not found.",
            )

        # ----------------------------------------------------
        # Ownership check
        # ----------------------------------------------------

        if str(sos.user_id) != str(
            user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this SOS.",
            )

        return {
            "success": True,
            "sos": sos,
        }

    except HTTPException:
        raise

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# ============================================================
# UPDATE SOS STATUS
# ============================================================

@router.patch(
    "/{sos_id}",
    response_model=SOSStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def update_sos_request(
    sos_id: str,
    payload: SOSUpdateRequest,
    current_user: Dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Update SOS lifecycle status.

    Example:

        active -> resolved
        active -> cancelled
    """

    user_id = get_authenticated_user_id(
        current_user
    )

    try:

        sos = await update_sos(
            sos_id=sos_id,
            payload=payload,
            requester_id=user_id,
        )

        if sos is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOS not found.",
            )

        return SOSStatusResponse(
            id=sos.id,
            status=sos.status,
            updated_at=sos.updated_at,
        )

    except HTTPException:
        raise

    except PermissionError as exc:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc