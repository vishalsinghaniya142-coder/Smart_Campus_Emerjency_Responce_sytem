from typing import Callable, List, Set

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.utils.jwt_handler import decode_access_token
from app.utils.response import error_response


# ============================================================
# PUBLIC ROUTES
# ============================================================
#
# These routes can be accessed without a JWT.
#
# IMPORTANT:
#
# Authentication middleware should NOT blindly protect every
# endpoint because:
#
#     /auth/register
#     /auth/login
#     /docs
#     /openapi.json
#     /health
#
# must be reachable before authentication.
# ============================================================

DEFAULT_PUBLIC_PATHS: Set[str] = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",

    "/auth/register",
    "/auth/login",
    "/auth/info",
    "/auth/firebase",
    "/prediction/analyze",
}


# ============================================================
# PUBLIC PATH PREFIXES
# ============================================================
#
# Some resources may have multiple sub-paths.
#
# Example:
#
#     /docs
#     /docs/oauth2-redirect
#
# Rather than hardcoding every child path, prefixes can be
# handled separately.
# ============================================================

DEFAULT_PUBLIC_PREFIXES: Set[str] = {
    "/docs/",
    "/redoc/",
    "/shelters",
}


# ============================================================
# HTTP METHODS
# ============================================================

SAFE_METHODS = {
    "OPTIONS",
}


# ============================================================
# AUTHENTICATION ERROR RESPONSE
# ============================================================

def authentication_error(
    message: str,
    error_code: str = "UNAUTHORIZED",
    status_code: int = 401,
) -> JSONResponse:
    """
    Create a standardized authentication error response.

    The response format is shared with:
        app/utils/response.py
    """

    body = error_response(
        message=message,
        error=error_code,
        status_code=status_code,
    )

    headers = {
        "WWW-Authenticate": "Bearer",
    }

    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
    )


# ============================================================
# AUTH MIDDLEWARE
# ============================================================

class AuthenticationMiddleware(
    BaseHTTPMiddleware
):
    """
    Application-level authentication middleware.

    Responsibilities
    ----------------
    1. Identify public endpoints.
    2. Allow public endpoints without authentication.
    3. Read Authorization header for protected requests.
    4. Verify Bearer token when authentication is enabled.
    5. Attach decoded authentication information to request.state.
    6. Allow route-level dependencies to perform final
       authorization/current-user checks.

    Important
    ---------
    This middleware does NOT replace:

        Depends(get_current_user)

    Route-level dependencies remain the authoritative way to
    require authentication for individual API routes.

    This middleware provides centralized request-level
    authentication context.
    """

    def __init__(
        self,
        app: ASGIApp,
        public_paths: Set[str] | None = None,
        public_prefixes: Set[str] | None = None,
    ):
        super().__init__(app)

        self.public_paths = (
            public_paths
            if public_paths is not None
            else DEFAULT_PUBLIC_PATHS.copy()
        )

        self.public_prefixes = (
            public_prefixes
            if public_prefixes is not None
            else DEFAULT_PUBLIC_PREFIXES.copy()
        )

    # ========================================================
    # PUBLIC PATH CHECK
    # ========================================================

    def is_public_path(
        self,
        path: str,
    ) -> bool:
        """
        Determine whether a request path is public.
        """

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        if path in self.public_paths:
            return True

        # ----------------------------------------------------
        # Prefix match
        # ----------------------------------------------------

        for prefix in self.public_prefixes:

            if path.startswith(prefix):
                return True

        return False

    # ========================================================
    # AUTHORIZATION HEADER PARSER
    # ========================================================

    @staticmethod
    def extract_bearer_token(
        authorization_header: str | None,
    ) -> str | None:
        """
        Extract JWT token from:

            Authorization: Bearer <token>

        Returns:
            token string
            None when no valid Bearer header is present
        """

        if not authorization_header:
            return None

        parts = authorization_header.strip().split(
            " ",
            maxsplit=1,
        )

        if len(parts) != 2:
            return None

        scheme, token = parts

        if scheme.lower() != "bearer":
            return None

        token = token.strip()

        if not token:
            return None

        return token

    # ========================================================
    # TOKEN VERIFICATION
    # ========================================================

    @staticmethod
    def verify_token(
        token: str,
    ) -> dict:
        """
        Decode and verify the JWT.

        The actual JWT cryptographic verification is delegated
        to:

            app/utils/jwt_handler.py
        """

        payload = decode_access_token(
            token
        )

        user_id = payload.get(
            "sub"
        )

        if not user_id:
            raise ValueError(
                "Authentication token does not contain a user ID."
            )

        return {
            "user_id": str(user_id),
            "email": payload.get("email"),
            "role": payload.get(
                "role",
                "user",
            ),
        }

    # ========================================================
    # REQUEST STATE
    # ========================================================

    @staticmethod
    def set_authenticated_state(
        request: Request,
        auth_data: dict,
    ) -> None:
        """
        Store authenticated-user information in request.state.

        Later routes/services can access:

            request.state.authenticated
            request.state.user_id
            request.state.user_email
            request.state.user_role
        """

        request.state.authenticated = True

        request.state.user_id = auth_data.get(
            "user_id"
        )

        request.state.user_email = auth_data.get(
            "email"
        )

        request.state.user_role = auth_data.get(
            "role",
            "user",
        )

    # ========================================================
    # ANONYMOUS REQUEST STATE
    # ========================================================

    @staticmethod
    def set_anonymous_state(
        request: Request,
    ) -> None:
        """
        Initialize request.state for an unauthenticated
        request.
        """

        request.state.authenticated = False

        request.state.user_id = None

        request.state.user_email = None

        request.state.user_role = None

    # ========================================================
    # REQUEST PROCESSING
    # ========================================================

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ):
        """
        Process every incoming HTTP request.

        Flow:

            Request
               |
               v
        Is public path?
          /       \
        yes       no
         |         |
         v         v
       allow    read JWT
                   |
                   v
              verify token
                   |
             +-----+-----+
             |           |
           valid       invalid
             |           |
             v           v
        request.state   401
             |
             v
         next layer
        """

        # ----------------------------------------------------
        # Initialize anonymous state.
        # ----------------------------------------------------

        self.set_anonymous_state(
            request
        )

        # ----------------------------------------------------
        # OPTIONS / CORS preflight
        # ----------------------------------------------------
        #
        # Browser CORS preflight requests should be allowed to
        # reach the CORS middleware instead of being blocked by
        # authentication.
        # ----------------------------------------------------

        if request.method.upper() in SAFE_METHODS:

            return await call_next(
                request
            )

        # ----------------------------------------------------
        # Authentication disabled
        # ----------------------------------------------------
        #
        # Useful during initial development.
        #
        # Production should use:
        #
        #     ENABLE_AUTH=true
        # ----------------------------------------------------

        if not settings.ENABLE_AUTH:

            request.state.authenticated = False

            request.state.auth_disabled = True

            return await call_next(
                request
            )

        # ----------------------------------------------------
        # Public route
        # ----------------------------------------------------

        if self.is_public_path(
            request.url.path
        ):

            request.state.public_endpoint = True

            return await call_next(
                request
            )

        # ----------------------------------------------------
        # Protected request
        # ----------------------------------------------------

        request.state.public_endpoint = False

        authorization_header = request.headers.get(
            "Authorization"
        )

        # ----------------------------------------------------
        # Missing Authorization header
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # We return 401 here for protected paths.
        #
        # This gives the API a consistent authentication
        # boundary.
        # ----------------------------------------------------

        if not authorization_header:

            return authentication_error(
                message="Authentication credentials are required.",
            )

        # ----------------------------------------------------
        # Extract Bearer token
        # ----------------------------------------------------

        token = self.extract_bearer_token(
            authorization_header
        )

        if token is None:

            return authentication_error(
                message="Authorization header must use Bearer authentication.",
            )

        # ----------------------------------------------------
        # Verify token
        # ----------------------------------------------------

        try:

            auth_data = self.verify_token(
                token
            )

        except ValueError:

            return authentication_error(
                message="Invalid or expired authentication token.",
            )

        except Exception:

            return authentication_error(
                message="Authentication could not be verified.",
            )

        # ----------------------------------------------------
        # Store authentication context
        # ----------------------------------------------------

        self.set_authenticated_state(
            request,
            auth_data,
        )

        # ----------------------------------------------------
        # Continue request
        # ----------------------------------------------------

        return await call_next(
            request
        )


# ============================================================
# ADD AUTHENTICATION MIDDLEWARE
# ============================================================

def configure_authentication_middleware(
    application,
) -> object:
    """
    Add AuthenticationMiddleware to the FastAPI application.

    Usage from main.py:

        configure_authentication_middleware(app)

    Returns:
        FastAPI application instance.
    """

    application.add_middleware(
        AuthenticationMiddleware
    )

    return application


# ============================================================
# PUBLIC PATH MANAGEMENT
# ============================================================

def add_public_path(
    path: str,
) -> None:
    """
    Add an exact path to the default public-path set.

    Example:

        add_public_path("/some-public-endpoint")
    """

    if not isinstance(path, str):
        raise ValueError(
            "Public path must be a string."
        )

    path = path.strip()

    if not path:
        raise ValueError(
            "Public path cannot be empty."
        )

    if not path.startswith("/"):
        path = "/" + path

    DEFAULT_PUBLIC_PATHS.add(
        path
    )


# ============================================================
# PUBLIC PREFIX MANAGEMENT
# ============================================================

def add_public_prefix(
    prefix: str,
) -> None:
    """
    Add a prefix to the default public-prefix set.
    """

    if not isinstance(prefix, str):
        raise ValueError(
            "Public prefix must be a string."
        )

    prefix = prefix.strip()

    if not prefix:
        raise ValueError(
            "Public prefix cannot be empty."
        )

    if not prefix.startswith("/"):
        prefix = "/" + prefix

    DEFAULT_PUBLIC_PREFIXES.add(
        prefix
    )


# ============================================================
# REMOVE PUBLIC PATH
# ============================================================

def remove_public_path(
    path: str,
) -> None:
    """
    Remove an exact path from the default public-path set.
    """

    DEFAULT_PUBLIC_PATHS.discard(
        path
    )


# ============================================================
# GET PUBLIC PATHS
# ============================================================

def get_public_paths() -> List[str]:
    """
    Return a sorted list of configured public paths.
    """

    return sorted(
        DEFAULT_PUBLIC_PATHS
    )


# ============================================================
# GET PUBLIC PREFIXES
# ============================================================

def get_public_prefixes() -> List[str]:
    """
    Return a sorted list of configured public prefixes.
    """

    return sorted(
        DEFAULT_PUBLIC_PREFIXES
    )