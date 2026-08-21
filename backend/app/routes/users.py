from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.services.auth_service import (
    get_user_by_id,
    update_user,
)
from app.schemas.auth_schema import (
    AuthUserResponse,
)
from app.utils.response import (
    resource_response,
    updated_response,
)
from app.utils.validators import (
    validate_name,
    validate_email,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# GET CURRENT USER PROFILE
# ============================================================

@router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
)
async def get_profile(
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Get the currently authenticated user's profile.

    Endpoint
    --------
    GET /users/profile

    Authentication
    --------------
    Bearer JWT required.

    Flow
    ----

        Frontend
            |
            | Authorization: Bearer <JWT>
            v
        auth_middleware.py
            |
            v
        dependencies.py
            |
            v
        get_current_user()
            |
            v
        users.py
            |
            v
        auth_service.py
            |
            v
        UserRepository
            |
            v
        Firebase / Database
            |
            v
        UserPublic
            |
            v
        Frontend
    """

    # --------------------------------------------------------
    # Extract authenticated user ID.
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Fetch complete public user profile.
    # --------------------------------------------------------

    user = await get_user_by_id(
        user_id
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile was not found.",
        )

    # --------------------------------------------------------
    # Return standardized response.
    # --------------------------------------------------------

    return resource_response(
        data=user.model_dump(
            mode="json"
        ),
        message="User profile fetched successfully.",
    )


# ============================================================
# GET CURRENT USER BASIC INFORMATION
# ============================================================

@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Return the authenticated user's information available from
    the authentication context.

    Endpoint
    --------
    GET /users/me

    This endpoint is intentionally lightweight.

    It uses the information already extracted from the JWT
    rather than requiring another database lookup.
    """

    user_id = current_user.get(
        "id"
    )

    email = current_user.get(
        "email"
    )

    role = current_user.get(
        "role",
        "user",
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return resource_response(
        data={
            "id": str(user_id),
            "email": email,
            "role": role,
        },
        message="Authenticated user information fetched successfully.",
    )


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================

@router.patch(
    "/profile",
    status_code=status.HTTP_200_OK,
)
async def update_profile(
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Update the authenticated user's profile.

    Endpoint
    --------
    PATCH /users/profile

    Currently supported fields:

        name
        email

    Role/status changes should normally be restricted to
    administrative operations and are therefore not accepted
    through this public profile endpoint.
    """

    # --------------------------------------------------------
    # Extract user ID from authentication context.
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Validate request body.
    # --------------------------------------------------------

    if not isinstance(
        payload,
        dict,
    ):

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Profile update data must be an object.",
        )

    if not payload:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile fields were provided.",
        )

    # --------------------------------------------------------
    # Only allow profile-editable fields.
    # --------------------------------------------------------

    allowed_fields = {
        "name",
        "email",
    }

    unsupported_fields = (
        set(payload.keys())
        - allowed_fields
    )

    if unsupported_fields:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported profile fields: "
                + ", ".join(
                    sorted(
                        str(field)
                        for field in unsupported_fields
                    )
                )
            ),
        )

    # --------------------------------------------------------
    # Build sanitized update dictionary.
    # --------------------------------------------------------

    updates: dict[str, Any] = {}

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    if "name" in payload:

        name = payload.get(
            "name"
        )

        if not isinstance(
            name,
            str,
        ):

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Name must be a string.",
            )

        try:

            updates["name"] = validate_name(
                name,
                field_name="Name",
            )

        except ValueError as exc:

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    if "email" in payload:

        email = payload.get(
            "email"
        )

        if not isinstance(
            email,
            str,
        ):

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Email must be a string.",
            )

        try:

            updates["email"] = validate_email(
                email
            )

        except ValueError as exc:

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    # --------------------------------------------------------
    # Make sure something remains after validation.
    # --------------------------------------------------------

    if not updates:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid profile fields were provided.",
        )

    # --------------------------------------------------------
    # Update through service layer.
    # --------------------------------------------------------

    try:

        updated_user = await update_user(
            user_id=user_id,
            updates=updates,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update user profile.",
        ) from exc

    # --------------------------------------------------------
    # User not found.
    # --------------------------------------------------------

    if updated_user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile was not found.",
        )

    # --------------------------------------------------------
    # Return updated profile.
    # --------------------------------------------------------

    return updated_response(
        data=updated_user.model_dump(
            mode="json"
        ),
        message="User profile updated successfully.",
    )


# ============================================================
# USER ROUTE INFORMATION
# ============================================================

@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
)
async def users_api_info() -> dict[str, Any]:
    """
    Development information about user endpoints.

    This endpoint is intentionally public and does not expose
    user information.
    """

    return {
        "success": True,
        "status": "success",
        "message": "Users API information.",
        "data": {
            "endpoints": {
                "profile": {
                    "method": "GET",
                    "path": "/users/profile",
                    "authentication": True,
                },
                "current_user": {
                    "method": "GET",
                    "path": "/users/me",
                    "authentication": True,
                },
                "update_profile": {
                    "method": "PATCH",
                    "path": "/users/profile",
                    "authentication": True,
                },
            }
        },
    }