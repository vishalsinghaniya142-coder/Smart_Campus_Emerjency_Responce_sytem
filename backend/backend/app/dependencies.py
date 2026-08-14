from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.utils.jwt_handler import decode_access_token


# ============================================================
# HTTP BEARER SECURITY
# ============================================================
#
# Frontend login ke baad JWT token receive karega.
#
# Example request:
#
# Authorization: Bearer eyJhbGciOiJIUzI1Ni...
#
# FastAPI HTTPBearer automatically Authorization header
# ko read karne mein help karega.
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# OPTIONAL AUTHENTICATION
# ============================================================

async def get_optional_credentials(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security
    ),
) -> Optional[str]:
    """
    Get the JWT token from the Authorization header.

    This dependency does NOT force authentication.

    If a token is available:
        return token

    If no token is available:
        return None

    This is useful for endpoints where authentication may
    be optional.
    """

    if credentials is None:
        return None

    if credentials.scheme.lower() != "bearer":
        return None

    return credentials.credentials


# ============================================================
# REQUIRED AUTHENTICATION
# ============================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security
    ),
):
    """
    Authenticate the current request.

    Expected header:

        Authorization: Bearer <JWT_TOKEN>

    Flow:

        Frontend
            |
            | Authorization header
            v
        FastAPI
            |
            v
        dependencies.py
            |
            v
        jwt_handler.py
            |
            v
        decoded token
            |
            v
        current user information
            |
            v
        protected route

    If the token is missing or invalid, the request is rejected.
    """

    # --------------------------------------------------------
    # AUTHENTICATION DISABLED
    # --------------------------------------------------------
    #
    # This is useful during early development/testing.
    #
    # In production ENABLE_AUTH should remain True.
    # --------------------------------------------------------

    if not settings.ENABLE_AUTH:
        return {
            "id": None,
            "email": None,
            "role": "development",
            "authenticated": False,
        }

    # --------------------------------------------------------
    # TOKEN MISSING
    # --------------------------------------------------------

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # VERIFY BEARER SCHEME
    # --------------------------------------------------------

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    token = credentials.credentials

    # --------------------------------------------------------
    # DECODE JWT
    # --------------------------------------------------------

    try:
        payload = decode_access_token(token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # PAYLOAD VALIDATION
    # --------------------------------------------------------

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # USER IDENTIFIER
    # --------------------------------------------------------
    #
    # Our JWT implementation will store the user identifier
    # inside the "sub" claim.
    #
    # Example payload:
    #
    # {
    #     "sub": "user_123",
    #     "email": "user@example.com",
    #     "role": "student"
    # }
    # --------------------------------------------------------

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token does not contain a user identifier.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # --------------------------------------------------------
    # CURRENT USER OBJECT
    # --------------------------------------------------------
    #
    # We intentionally return a simple authenticated-user
    # representation here.
    #
    # Actual user retrieval/storage will be handled by the
    # appropriate service/database layer.
    # --------------------------------------------------------

    current_user = {
        "id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "authenticated": True,
    }

    return current_user


# ============================================================
# CURRENT USER ID
# ============================================================

async def get_current_user_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    """
    Return only the authenticated user's ID.

    Useful for routes where we only need the user identifier.

    Example:

        @router.get("/profile")
        async def profile(
            user_id: str = Depends(get_current_user_id)
        ):
            ...
    """

    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is unavailable.",
        )

    return str(user_id)


# ============================================================
# CURRENT USER EMAIL
# ============================================================

async def get_current_user_email(
    current_user: dict = Depends(get_current_user),
) -> str:
    """
    Return the authenticated user's email address.

    This dependency is useful when a route needs the email
    but does not need the complete current-user object.
    """

    email = current_user.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user email is unavailable.",
        )

    return str(email)


# ============================================================
# ROLE CHECKER
# ============================================================

def require_role(required_role: str):
    """
    Create a dependency that requires a specific user role.

    Example:

        admin_required = require_role("admin")

        @router.get("/admin-area")
        async def admin_area(
            current_user: dict = Depends(admin_required)
        ):
            ...
    """

    async def role_dependency(
        current_user: dict = Depends(get_current_user),
    ):
        user_role = current_user.get("role")

        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return role_dependency


# ============================================================
# ADMIN USER DEPENDENCY
# ============================================================

async def get_current_admin(
    current_user: dict = Depends(get_current_user),
):
    """
    Require the currently authenticated user to have admin role.

    This will be useful later if an admin dashboard or
    administrative endpoints are added.
    """

    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required.",
        )

    return current_user


# ============================================================
# ACTIVE USER DEPENDENCY
# ============================================================

async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
):
    """
    Return the current authenticated user.

    This function is intentionally kept as a separate
    dependency so that account-status checks can be added later
    without changing every protected route.

    Example future user payload:

        {
            "id": "123",
            "email": "user@example.com",
            "role": "student",
            "is_active": True
        }
    """

    # --------------------------------------------------------
    # Future account-status validation
    # --------------------------------------------------------
    #
    # Once the User model/service is implemented, this is where
    # we can verify:
    #
    #     is_active
    #     account_disabled
    #     account_verified
    #
    # For now, authenticated users are treated as active.
    # --------------------------------------------------------

    return current_user


# ============================================================
# DEVELOPMENT USER
# ============================================================

async def get_development_user():
    """
    Return a development-only user representation.

    This helper should NOT be used for production
    authentication.

    It can be useful while building/testing routes before the
    complete authentication flow is connected.
    """

    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development user is only available in development mode.",
        )

    return {
        "id": "development-user",
        "email": "development@example.com",
        "role": "developer",
        "authenticated": False,
    }