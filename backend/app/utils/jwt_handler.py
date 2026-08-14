from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.config import settings


# ============================================================
# JWT CLAIM NAMES
# ============================================================
#
# Standard JWT:
#
# sub  -> subject / user identifier
# exp  -> expiration time
# iat  -> issued-at time
#
# We will also use:
#
# email -> authenticated user's email
# role  -> user's application role
#
# Example payload:
#
# {
#     "sub": "user_123",
#     "email": "user@example.com",
#     "role": "student",
#     "iat": 1234567890,
#     "exp": 1234567890
# }
# ============================================================

SUBJECT_CLAIM = "sub"
EMAIL_CLAIM = "email"
ROLE_CLAIM = "role"
ISSUED_AT_CLAIM = "iat"
EXPIRATION_CLAIM = "exp"


# ============================================================
# UTC TIME HELPER
# ============================================================

def get_current_utc_time() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.

    JWT expiration calculations should use UTC so that the
    backend behaves consistently across different locations
    and deployment environments.
    """

    return datetime.now(timezone.utc)


# ============================================================
# TOKEN EXPIRATION
# ============================================================

def get_access_token_expiration(
    expires_minutes: Optional[int] = None,
) -> datetime:
    """
    Calculate the expiration datetime for an access token.

    If expires_minutes is not provided, the value configured
    in settings is used.
    """

    if expires_minutes is None:
        expires_minutes = (
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    if expires_minutes <= 0:
        raise ValueError(
            "JWT token expiration must be greater than zero minutes."
        )

    return (
        get_current_utc_time()
        + timedelta(minutes=expires_minutes)
    )


# ============================================================
# CREATE JWT PAYLOAD
# ============================================================

def create_token_payload(
    user_id: str,
    email: Optional[str] = None,
    role: str = "user",
    expires_minutes: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create the payload used to generate a JWT.

    Parameters
    ----------
    user_id:
        Unique identifier of the authenticated user.

    email:
        User's email address.

    role:
        Application role such as:
            user
            student
            admin

    expires_minutes:
        Optional custom expiration period.

    extra_claims:
        Optional additional claims.

    Returns
    -------
    dict
        JWT payload.
    """

    if not user_id:
        raise ValueError(
            "user_id is required to create a JWT payload."
        )

    if not role:
        role = "user"

    current_time = get_current_utc_time()

    expiration_time = get_access_token_expiration(
        expires_minutes
    )

    payload: Dict[str, Any] = {
        SUBJECT_CLAIM: str(user_id),
        ROLE_CLAIM: role,
        ISSUED_AT_CLAIM: current_time,
        EXPIRATION_CLAIM: expiration_time,
    }

    if email:
        payload[EMAIL_CLAIM] = email

    # --------------------------------------------------------
    # Additional application-specific claims
    # --------------------------------------------------------

    if extra_claims:
        for key, value in extra_claims.items():

            # Prevent callers from accidentally replacing
            # security-critical standard claims.
            if key in {
                SUBJECT_CLAIM,
                ISSUED_AT_CLAIM,
                EXPIRATION_CLAIM,
            }:
                continue

            payload[key] = value

    return payload


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================

def create_access_token(
    user_id: str,
    email: Optional[str] = None,
    role: str = "user",
    expires_minutes: Optional[int] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create and sign a JWT access token.

    Flow:

        User Login
            |
            v
        auth route
            |
            v
        auth service
            |
            v
        create_access_token()
            |
            v
        signed JWT
            |
            v
        frontend

    The frontend can then send this token in:

        Authorization: Bearer <token>
    """

    payload = create_token_payload(
        user_id=user_id,
        email=email,
        role=role,
        expires_minutes=expires_minutes,
        extra_claims=extra_claims,
    )

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


# ============================================================
# DECODE ACCESS TOKEN
# ============================================================

def decode_access_token(
    token: str,
) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token.

    This function is used by:

        app/dependencies.py

    to authenticate protected endpoints.

    Raises
    ------
    ValueError
        When the token is missing, invalid or expired.

    Returns
    -------
    dict
        Decoded JWT payload.
    """

    if not token:
        raise ValueError(
            "Access token is required."
        )

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

    except JWTError as exc:

        raise ValueError(
            "Invalid or expired access token."
        ) from exc

    # --------------------------------------------------------
    # Validate user identifier
    # --------------------------------------------------------

    user_id = payload.get(
        SUBJECT_CLAIM
    )

    if not user_id:
        raise ValueError(
            "Access token does not contain a user identifier."
        )

    # --------------------------------------------------------
    # Validate expiration manually as an additional check.
    #
    # python-jose also validates exp during decode, but keeping
    # this explicit check makes the authentication contract
    # clear and protects us if token handling changes later.
    # --------------------------------------------------------

    expiration = payload.get(
        EXPIRATION_CLAIM
    )

    if expiration is None:
        raise ValueError(
            "Access token does not contain an expiration time."
        )

    try:

        expiration_timestamp = float(
            expiration
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "Invalid access token expiration."
        ) from exc

    current_timestamp = (
        get_current_utc_time().timestamp()
    )

    if expiration_timestamp <= current_timestamp:
        raise ValueError(
            "Access token has expired."
        )

    return payload


# ============================================================
# GET USER ID FROM TOKEN
# ============================================================

def get_user_id_from_token(
    token: str,
) -> str:
    """
    Decode a JWT and return the authenticated user's ID.
    """

    payload = decode_access_token(
        token
    )

    user_id = payload.get(
        SUBJECT_CLAIM
    )

    if not user_id:
        raise ValueError(
            "User ID is missing from access token."
        )

    return str(user_id)


# ============================================================
# GET USER EMAIL FROM TOKEN
# ============================================================

def get_user_email_from_token(
    token: str,
) -> Optional[str]:
    """
    Decode a JWT and return the user's email.

    Email may be unavailable for tokens created without an
    email claim, so this function returns None in that case.
    """

    payload = decode_access_token(
        token
    )

    email = payload.get(
        EMAIL_CLAIM
    )

    if email is None:
        return None

    return str(email)


# ============================================================
# GET USER ROLE FROM TOKEN
# ============================================================

def get_user_role_from_token(
    token: str,
) -> str:
    """
    Decode a JWT and return the user's role.

    If no role was stored, the default role is "user".
    """

    payload = decode_access_token(
        token
    )

    role = payload.get(
        ROLE_CLAIM,
        "user",
    )

    return str(role)


# ============================================================
# CHECK TOKEN VALIDITY
# ============================================================

def is_token_valid(
    token: str,
) -> bool:
    """
    Check whether a JWT is valid.

    Returns:
        True  -> valid token
        False -> invalid/expired token

    This helper does not raise authentication exceptions.
    It is useful for internal checks and tests.
    """

    if not token:
        return False

    try:

        decode_access_token(
            token
        )

        return True

    except (
        ValueError,
        JWTError,
    ):

        return False


# ============================================================
# GET TOKEN EXPIRATION
# ============================================================

def get_token_expiration(
    token: str,
) -> Optional[datetime]:
    """
    Get the expiration time from a valid JWT.

    Returns:
        timezone-aware UTC datetime

    Returns None when the token is invalid or does not contain
    a valid expiration claim.
    """

    try:

        payload = decode_access_token(
            token
        )

    except ValueError:
        return None

    expiration = payload.get(
        EXPIRATION_CLAIM
    )

    if expiration is None:
        return None

    try:

        expiration_timestamp = float(
            expiration
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    return datetime.fromtimestamp(
        expiration_timestamp,
        tz=timezone.utc,
    )


# ============================================================
# CHECK TOKEN EXPIRATION
# ============================================================

def is_token_expired(
    token: str,
) -> bool:
    """
    Determine whether a token is expired.

    Invalid tokens are treated as expired for security.
    """

    expiration = get_token_expiration(
        token
    )

    if expiration is None:
        return True

    return (
        expiration
        <= get_current_utc_time()
    )


# ============================================================
# SANITIZE TOKEN PAYLOAD
# ============================================================

def get_safe_token_payload(
    token: str,
) -> Dict[str, Any]:
    """
    Return only the application-level information that the
    backend needs from a JWT.

    Sensitive/internal JWT details are not unnecessarily
    exposed to route logic.
    """

    payload = decode_access_token(
        token
    )

    return {
        "user_id": str(
            payload.get(
                SUBJECT_CLAIM
            )
        ),
        "email": payload.get(
            EMAIL_CLAIM
        ),
        "role": payload.get(
            ROLE_CLAIM,
            "user",
        ),
    }