from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
)
from app.utils.response import (
    authentication_response,
    created_response,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
) -> dict[str, Any]:
    """
    Register a new user.

    Endpoint
    --------
    POST /auth/register

    Request
    -------
    The frontend sends registration information.

    Flow
    ----
        Frontend
            |
            v
        POST /auth/register
            |
            v
        auth.py
            |
            v
        auth_service.py
            |
            +----> validation
            |
            +----> password handling
            |
            +----> user creation
            |
            v
        authentication/user result
            |
            v
        Frontend

    IMPORTANT:
        Database implementation does not belong inside this
        route.
    """

    try:

        result = await register_user(
            payload
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register user.",
        ) from exc

    return created_response(
        data=result,
        message="User registered successfully.",
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
) -> dict[str, Any]:
    """
    Authenticate an existing user.

    Endpoint
    --------
    POST /auth/login

    Request
    -------
    The frontend sends login credentials.

    Flow
    ----
        Frontend
            |
            v
        POST /auth/login
            |
            v
        auth.py
            |
            v
        auth_service.py
            |
            +----> find user
            |
            +----> verify password
            |
            +----> create JWT
            |
            v
        access token
            |
            v
        Frontend

    The frontend will later use the returned JWT as:

        Authorization: Bearer <access_token>
    """

    try:

        result = await authenticate_user(
            payload
        )

    except ValueError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to authenticate user.",
        ) from exc

    # --------------------------------------------------------
    # Expected service result
    # --------------------------------------------------------
    #
    # auth_service.py will eventually return something like:
    #
    # {
    #     "user": {...},
    #     "access_token": "...",
    # }
    #
    # We keep token formatting here so that the service remains
    # responsible for authentication logic while the route
    # remains responsible for HTTP/API presentation.
    # --------------------------------------------------------

    if not isinstance(
        result,
        dict,
    ):

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid authentication service response.",
        )

    user = result.get(
        "user"
    )

    access_token = result.get(
        "access_token"
    )

    if not access_token:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication token was not generated.",
        )

    return authentication_response(
        user=user,
        access_token=access_token,
        message="Login successful.",
        token_type="bearer",
    )


# ============================================================
# AUTH ROUTE INFORMATION
# ============================================================

@router.get(
    "/info",
)
async def authentication_info() -> dict[str, Any]:
    """
    Return basic information about authentication endpoints.

    This is primarily useful during development and integration
    testing.

    It does not expose credentials or secret configuration.
    """

    return {
        "success": True,
        "status": "success",
        "message": "Authentication API information.",
        "data": {
            "endpoints": {
                "register": {
                    "method": "POST",
                    "path": "/auth/register",
                },
                "login": {
                    "method": "POST",
                    "path": "/auth/login",
                },
            },
            "authentication_type": "Bearer JWT",
        },
    }