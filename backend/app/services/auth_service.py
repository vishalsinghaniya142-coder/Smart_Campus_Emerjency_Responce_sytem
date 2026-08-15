from datetime import datetime, timezone
from typing import Optional, Protocol, Dict, Any

from passlib.context import CryptContext

from app.config import settings
from app.models.user import (
    UserAuthentication,
    UserCreate,
    UserPublic,
    build_user,
    user_to_public,
)
from app.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
)
from app.utils.jwt_handler import create_access_token
from app.utils.validators import (
    validate_email,
    validate_password,
    validate_user_role,
)


# ============================================================
# PASSWORD HASHING
# ============================================================
#
# Passwords must NEVER be stored as plain text.
#
# Registration:
#
#     plain password
#          |
#          v
#     hash_password()
#          |
#          v
#     password_hash
#          |
#          v
#     database
#
# Login:
#
#     plain password
#          |
#          v
#     verify_password()
#          |
#          v
#     password_hash
# ============================================================

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(
    password: str,
) -> str:
    """
    Hash a plain-text password.

    The plain password should only exist temporarily during
    registration/login and must never be persisted.
    """

    validated_password = validate_password(
        password
    )

    return password_context.hash(
        validated_password
    )


def verify_password(
    plain_password: str,
    password_hash: str,
) -> bool:
    """
    Verify a plain-text password against a stored password hash.

    Returns:
        True  -> password matches
        False -> password does not match
    """

    if not plain_password:
        return False

    if not password_hash:
        return False

    try:

        return password_context.verify(
            plain_password,
            password_hash,
        )

    except Exception:
        return False


# ============================================================
# USER REPOSITORY CONTRACT
# ============================================================
#
# IMPORTANT ARCHITECTURE:
#
# auth_service.py does NOT directly talk to Firebase.
#
# Instead:
#
#     auth_service
#          |
#          v
#     UserRepository
#          |
#          v
#     Member 4 database integration
#          |
#          v
#     Firebase
#
# This Protocol defines what the backend expects from the
# database layer.
#
# Later Member 4 can implement this contract using Firebase.
# ============================================================

class UserRepository(Protocol):
    """
    Contract that a user database/integration implementation
    must follow.

    This is intentionally database-agnostic.
    """

    async def create_user(
        self,
        user: UserAuthentication,
    ) -> UserAuthentication:
        """
        Persist a new user and return the stored user.
        """
        ...

    async def get_user_by_email(
        self,
        email: str,
    ) -> Optional[UserAuthentication]:
        """
        Find a user using their email.
        """
        ...

    async def get_user_by_id(
        self,
        user_id: str,
    ) -> Optional[UserAuthentication]:
        """
        Find a user using their unique ID.
        """
        ...

    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[UserAuthentication]:
        """
        Update an existing user.
        """
        ...


# ============================================================
# REPOSITORY INSTANCE
# ============================================================
#
# Initially None because the actual database implementation
# belongs to the integration/database layer.
#
# This prevents us from incorrectly putting Firebase logic
# inside Member 2's backend service.
# ============================================================
# ============================================================
# DATABASE USER REPOSITORY
# ============================================================
#
# The concrete database implementation will be provided by
# the database layer.
#
# auth_service.py only depends on the UserRepository contract.
# Firebase/Firestore will be connected during application
# startup.
# ============================================================

_user_repository: Optional[UserRepository] = None
# ============================================================

# ============================================================
# CONFIGURE USER REPOSITORY
# ============================================================

def configure_user_repository(
    repository: UserRepository,
) -> None:
    """
    Register the concrete user repository.

    Example future integration:

        from services.database.users import FirebaseUserRepository

        configure_user_repository(
            FirebaseUserRepository(...)
        )

    The actual Firebase implementation will belong to the
    database/integration layer, not this authentication service.
    """

    global _user_repository

    if repository is None:
        raise ValueError(
            "User repository cannot be None."
        )

    _user_repository = repository


# ============================================================
# GET USER REPOSITORY
# ============================================================

def get_user_repository() -> UserRepository:
    """
    Return the configured user repository.

    Raises:
        RuntimeError:
            When database integration has not yet been connected.
    """

    if _user_repository is None:

        raise RuntimeError(
            "User repository is not configured. "
            "Connect the database integration before using "
            "authentication operations."
        )

    return _user_repository


# ============================================================
# NORMALIZE REGISTRATION DATA
# ============================================================

def normalize_registration_data(
    payload: RegisterRequest,
) -> UserCreate:
    """
    Normalize and validate registration input.

    This function converts the API schema into the internal
    UserCreate model used by the authentication service.
    """

    name = payload.name.strip()

    email = validate_email(
        str(payload.email)
    )

    password = validate_password(
        payload.password
    )

    role = validate_user_role(
        payload.role or "student"
    )

    return UserCreate(
        name=name,
        email=email,
        password=password,
        role=role,
    )


# ============================================================
# CHECK EMAIL AVAILABILITY
# ============================================================

async def email_exists(
    email: str,
) -> bool:
    """
    Check whether an email is already registered.
    """

    repository = get_user_repository()

    normalized_email = validate_email(
        email
    )

    existing_user = (
        await repository.get_user_by_email(
            normalized_email
        )
    )

    return existing_user is not None


# ============================================================
# REGISTER USER
# ============================================================

async def register_user(
    payload: RegisterRequest,
) -> Dict[str, Any]:
    """
    Register a new user.

    Complete flow:

        RegisterRequest
              |
              v
        validate/normalize
              |
              v
        check duplicate email
              |
              v
        hash password
              |
              v
        UserAuthentication
              |
              v
        UserRepository
              |
              v
        Database / Firebase
              |
              v
        UserPublic
              |
              v
        Route response
    """

    # --------------------------------------------------------
    # Normalize and validate input
    # --------------------------------------------------------

    user_data = normalize_registration_data(
        payload
    )

    # --------------------------------------------------------
    # Get database repository
    # --------------------------------------------------------

    repository = get_user_repository()

    # --------------------------------------------------------
    # Check duplicate email
    # --------------------------------------------------------

    existing_user = (
        await repository.get_user_by_email(
            user_data.email
        )
    )

    if existing_user is not None:

        raise ValueError(
            "An account with this email already exists."
        )

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = hash_password(
        user_data.password
    )

    # --------------------------------------------------------
    # Generate temporary/application user ID
    # --------------------------------------------------------
    #
    # The final database integration may replace this ID with
    # its own generated identifier.
    #
    # We deliberately avoid depending on Firebase here.
    # --------------------------------------------------------

    user_id = generate_user_id(
        user_data.email
    )

    # --------------------------------------------------------
    # Current timestamps
    # --------------------------------------------------------

    current_time = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Build internal authentication model
    # --------------------------------------------------------

    user = UserAuthentication(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        is_active=True,
        is_verified=False,
        created_at=current_time,
        updated_at=current_time,
    )

    # --------------------------------------------------------
    # Persist user
    # --------------------------------------------------------

    stored_user = await repository.create_user(
        user
    )

    # --------------------------------------------------------
    # Convert to safe public representation
    # --------------------------------------------------------

    public_user = UserPublic(
        id=stored_user.id,
        name=stored_user.name,
        email=stored_user.email,
        role=stored_user.role,
        is_active=stored_user.is_active,
        is_verified=stored_user.is_verified,
        created_at=stored_user.created_at,
        updated_at=stored_user.updated_at,
    )

    return {
        "user": public_user.model_dump(
            mode="json"
        ),
    }


# ============================================================
# AUTHENTICATE USER
# ============================================================

async def authenticate_user(
    payload: LoginRequest,
) -> Dict[str, Any]:
    """
    Authenticate a user and generate a JWT.

    Complete flow:

        LoginRequest
             |
             v
        normalize email
             |
             v
        UserRepository
             |
             v
        stored user
             |
             v
        verify password
             |
             v
        check account
             |
             v
        create JWT
             |
             v
        return user + token
    """

    # --------------------------------------------------------
    # Normalize email
    # --------------------------------------------------------

    email = validate_email(
        str(payload.email)
    )

    # --------------------------------------------------------
    # Validate supplied password
    # --------------------------------------------------------

    password = payload.password

    if not password:
        raise ValueError(
            "Password is required."
        )

    # --------------------------------------------------------
    # Get repository
    # --------------------------------------------------------

    repository = get_user_repository()

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = await repository.get_user_by_email(
        email
    )

    # --------------------------------------------------------
    # Do not reveal whether email exists.
    #
    # The route will return the same authentication failure
    # message for invalid email/password.
    # --------------------------------------------------------

    if user is None:

        raise ValueError(
            "Invalid email or password."
        )

    # --------------------------------------------------------
    # Verify account status
    # --------------------------------------------------------

    if not user.is_active:

        raise ValueError(
            "This user account is inactive."
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_valid = verify_password(
        password,
        user.password_hash,
    )

    if not password_valid:

        raise ValueError(
            "Invalid email or password."
        )

    # --------------------------------------------------------
    # Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        user_id=user.id,
        email=str(user.email),
        role=user.role,
    )

    # --------------------------------------------------------
    # Convert user to public representation
    # --------------------------------------------------------

    public_user = UserPublic(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )

    return {
        "user": public_user.model_dump(
            mode="json"
        ),
        "access_token": access_token,
    }


# ============================================================
# GET USER BY ID
# ============================================================

async def get_user_by_id(
    user_id: str,
) -> Optional[UserPublic]:
    """
    Retrieve a user by ID and return only public information.

    This will later be used by:
        users.py
        incident ownership
        SOS ownership
        other protected services
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    repository = get_user_repository()

    user = await repository.get_user_by_id(
        user_id
    )

    if user is None:
        return None

    return UserPublic(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ============================================================
# GET USER FOR AUTHENTICATION
# ============================================================

async def get_authentication_user_by_id(
    user_id: str,
) -> Optional[UserAuthentication]:
    """
    Retrieve the internal authentication representation of a
    user.

    This function must only be used internally.

    password_hash must never be returned directly through an
    API endpoint.
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    repository = get_user_repository()

    return await repository.get_user_by_id(
        user_id
    )


# ============================================================
# UPDATE USER
# ============================================================

async def update_user(
    user_id: str,
    updates: Dict[str, Any],
) -> Optional[UserPublic]:
    """
    Update user information.

    Password updates are intentionally not handled here yet.

    A dedicated password-change flow should perform password
    verification and hashing explicitly.
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    if not isinstance(
        updates,
        dict,
    ):
        raise ValueError(
            "User updates must be provided as a dictionary."
        )

    repository = get_user_repository()

    sanitized_updates = {}

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    if "name" in updates:

        name = updates["name"]

        if not isinstance(
            name,
            str,
        ):
            raise ValueError(
                "Name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Name cannot be empty."
            )

        sanitized_updates["name"] = name

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    if "email" in updates:

        email = validate_email(
            str(updates["email"])
        )

        # Check if another user already uses the email.
        existing_user = (
            await repository.get_user_by_email(
                email
            )
        )

        if (
            existing_user is not None
            and existing_user.id != user_id
        ):

            raise ValueError(
                "Another account already uses this email."
            )

        sanitized_updates["email"] = email

    # --------------------------------------------------------
    # Role
    # --------------------------------------------------------

    if "role" in updates:

        sanitized_updates["role"] = (
            validate_user_role(
                str(updates["role"])
            )
        )

    # --------------------------------------------------------
    # Active status
    # --------------------------------------------------------

    if "is_active" in updates:

        if not isinstance(
            updates["is_active"],
            bool,
        ):
            raise ValueError(
                "is_active must be a boolean."
            )

        sanitized_updates["is_active"] = (
            updates["is_active"]
        )

    # --------------------------------------------------------
    # Verification status
    # --------------------------------------------------------

    if "is_verified" in updates:

        if not isinstance(
            updates["is_verified"],
            bool,
        ):
            raise ValueError(
                "is_verified must be a boolean."
            )

        sanitized_updates["is_verified"] = (
            updates["is_verified"]
        )

    # --------------------------------------------------------
    # Nothing to update
    # --------------------------------------------------------

    if not sanitized_updates:

        raise ValueError(
            "No valid user fields were provided for update."
        )

    # --------------------------------------------------------
    # Updated timestamp
    # --------------------------------------------------------

    sanitized_updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    # --------------------------------------------------------
    # Persist update
    # --------------------------------------------------------

    updated_user = await repository.update_user(
        user_id,
        sanitized_updates,
    )

    if updated_user is None:
        return None

    return UserPublic(
        id=updated_user.id,
        name=updated_user.name,
        email=updated_user.email,
        role=updated_user.role,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
    )


# ============================================================
# ACTIVATE USER
# ============================================================

async def activate_user(
    user_id: str,
) -> Optional[UserPublic]:
    """
    Activate a user account.
    """

    return await update_user(
        user_id,
        {
            "is_active": True,
        },
    )


# ============================================================
# DEACTIVATE USER
# ============================================================

async def deactivate_user(
    user_id: str,
) -> Optional[UserPublic]:
    """
    Deactivate a user account.
    """

    return await update_user(
        user_id,
        {
            "is_active": False,
        },
    )


# ============================================================
# VERIFY USER
# ============================================================

async def verify_user(
    user_id: str,
) -> Optional[UserPublic]:
    """
    Mark a user's account as verified.
    """

    return await update_user(
        user_id,
        {
            "is_verified": True,
        },
    )


# ============================================================
# GENERATE USER ID
# ============================================================

def generate_user_id(
    email: str,
) -> str:
    """
    Generate a temporary deterministic-style application user
    identifier.

    IMPORTANT:

    The final database integration may replace this with its
    own ID generation mechanism.

    This function deliberately does not depend on Firebase.

    The generated ID is NOT intended to be a cryptographic
    security identifier.
    """

    normalized_email = validate_email(
        email
    )

    # --------------------------------------------------------
    # Use a stable hash-like transformation without exposing
    # the full email address.
    # --------------------------------------------------------

    import hashlib

    digest = hashlib.sha256(
        normalized_email.encode(
            "utf-8"
        )
    ).hexdigest()

    return f"user_{digest[:24]}"


# ============================================================
# BUILD USER FROM REGISTRATION DATA
# ============================================================

def build_user_for_registration(
    payload: RegisterRequest,
) -> UserAuthentication:
    """
    Build an internal UserAuthentication object from a
    registration request.

    This helper does not persist the user.
    """

    user_data = normalize_registration_data(
        payload
    )

    password_hash = hash_password(
        user_data.password
    )

    current_time = datetime.now(
        timezone.utc
    )

    return UserAuthentication(
        id=generate_user_id(
            user_data.email
        ),
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        is_active=True,
        is_verified=False,
        created_at=current_time,
        updated_at=current_time,
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

async def change_password(
    user_id: str,
    current_password: str,
    new_password: str,
) -> bool:
    """
    Change an existing user's password.

    Flow:

        current password
              |
              v
        verify old hash
              |
              v
        validate new password
              |
              v
        hash new password
              |
              v
        update database
    """

    if not user_id:
        raise ValueError(
            "User ID is required."
        )

    if not current_password:
        raise ValueError(
            "Current password is required."
        )

    # --------------------------------------------------------
    # Validate new password
    # --------------------------------------------------------

    validated_new_password = validate_password(
        new_password
    )

    repository = get_user_repository()

    # --------------------------------------------------------
    # Get current user
    # --------------------------------------------------------

    user = await repository.get_user_by_id(
        user_id
    )

    if user is None:
        raise ValueError(
            "User not found."
        )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        current_password,
        user.password_hash,
    ):

        raise ValueError(
            "Current password is incorrect."
        )

    # --------------------------------------------------------
    # Hash new password
    # --------------------------------------------------------

    new_password_hash = hash_password(
        validated_new_password
    )

    # --------------------------------------------------------
    # Update password
    # --------------------------------------------------------

    updated_user = await repository.update_user(
        user_id,
        {
            "password_hash": new_password_hash,
            "updated_at": datetime.now(
                timezone.utc
            ),
        },
    )

    if updated_user is None:
        raise ValueError(
            "Unable to update password."
        )

    return True