from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.utils.validators import validate_user_role


# ============================================================
# USER MODEL
# ============================================================

class User(BaseModel):
    """
    Backend representation of a system user.

    IMPORTANT:
        This model does not directly connect to Firebase or any
        other database.

    Database persistence will be handled through the service /
    integration layer.

    This keeps the architecture:

        Route
          ↓
        Service
          ↓
        User model
          ↓
        Database integration
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    # --------------------------------------------------------
    # USER ID
    # --------------------------------------------------------

    id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Unique identifier of the user.",
        examples=["user_123"],
    )

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user.",
        examples=["Vishal Singh"],
    )

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    email: EmailStr = Field(
        ...,
        description="Unique email address of the user.",
        examples=["vishal@example.com"],
    )
    phone_number: str = Field(
    default="",
    max_length=20,
    description="Registered mobile number of the user.",
    )

    # --------------------------------------------------------
    # ROLE
    # --------------------------------------------------------

    role: str = Field(
        default="student",
        max_length=30,
        description="Application role of the user.",
        examples=["student"],
    )

    # --------------------------------------------------------
    # ACCOUNT STATUS
    # --------------------------------------------------------

    is_active: bool = Field(
        default=True,
        description="Whether the user account is active.",
    )

    is_verified: bool = Field(
        default=False,
        description="Whether the user's account has been verified.",
    )

    # --------------------------------------------------------
    # CREATED AT
    # --------------------------------------------------------

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ),
        description="UTC timestamp when the user was created.",
    )

    # --------------------------------------------------------
    # UPDATED AT
    # --------------------------------------------------------

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ),
        description="UTC timestamp when the user was last updated.",
    )


# ============================================================
# USER CREATION MODEL
# ============================================================

class UserCreate(BaseModel):
    """
    Internal model used when creating a new user.

    This model intentionally contains the password because it
    is needed temporarily during registration.

    IMPORTANT:
        Password must NEVER be stored directly in a User model.

    The auth service will:
        1. Validate password.
        2. Hash password.
        3. Store only the password hash through the database
           integration layer.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )
    phone_number: str = Field(
    ...,
    min_length=10,
    max_length=20,
    description="Registered mobile number.",
    )
    role: str = Field(
        default="student",
        max_length=30,
    )


# ============================================================
# USER UPDATE MODEL
# ============================================================

class UserUpdate(BaseModel):
    """
    Model for updating an existing user.

    All fields are optional because a profile update may modify
    only one field.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    email: Optional[EmailStr] = Field(
        default=None,
    )
    phone_number: Optional[str] = Field(
    default=None,
    min_length=10,
    max_length=20,
   )

    role: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    is_active: Optional[bool] = None

    is_verified: Optional[bool] = None


# ============================================================
# USER PUBLIC MODEL
# ============================================================

class UserPublic(BaseModel):
    """
    Safe representation of a user that can be returned to the
    frontend.

    Password and password hash are intentionally absent.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str

    name: str

    email: EmailStr

    phone_number: str

    role: str

    is_active: bool

    is_verified: bool

    created_at: datetime

    updated_at: datetime


# ============================================================
# USER AUTHENTICATION MODEL
# ============================================================

class UserAuthentication(BaseModel):
    """
    Internal representation used during authentication.

    This model may contain the password hash because the
    authentication service needs it to verify a login.

    IMPORTANT:
        This model must never be returned directly to the
        frontend.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str

    name: str

    email: EmailStr

    phone_number: str = ""

    password_hash: str

    role: str = "student"

    is_active: bool = True

    is_verified: bool = False

    created_at: datetime

    updated_at: datetime


# ============================================================
# USER DOCUMENT MODEL
# ============================================================

class UserDocument(BaseModel):
    """
    Representation of the data that can be persisted by a
    database service.

    This is intentionally database-agnostic.

    Member 4's Firebase implementation can convert this model
    into the appropriate Firebase document structure.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str

    name: str

    email: EmailStr

    phone_number: str = ""

    password_hash: str

    role: str = "student"

    is_active: bool = True

    is_verified: bool = False

    created_at: datetime

    updated_at: datetime


# ============================================================
# USER ROLE NORMALIZATION
# ============================================================

def normalize_user_role(
    role: Optional[str],
) -> str:
    """
    Normalize and validate a user role.

    If no role is supplied, 'student' is used as the default
    registration role.
    """

    if role is None:
        return "student"

    role = role.strip().lower()

    if not role:
        return "student"

    return validate_user_role(
        role
    )


# ============================================================
# CREATE USER OBJECT
# ============================================================

def build_user(
    user_id: str,
    name: str,
    email: str,
    phone_number: str = "",
    role: str = "student",
    is_active: bool = True,
    is_verified: bool = False,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> User:
    """
    Build a User domain object.

    This helper is useful when a database/integration service
    returns raw data and the backend needs to convert it into
    a validated User model.
    """

    now = datetime.now(
        timezone.utc
    )

    if created_at is None:
        created_at = now

    if updated_at is None:
        updated_at = now

    normalized_role = normalize_user_role(
        role
    )

    return User(
        id=str(user_id),
        name=name,
        email=email,
        phone_number=phone_number,
        role=normalized_role,
        is_active=is_active,
        is_verified=is_verified,
        created_at=created_at,
        updated_at=updated_at,
    )


# ============================================================
# BUILD USER FROM DOCUMENT
# ============================================================

def user_from_document(
    document: Dict[str, Any],
) -> User:
    """
    Convert a database/integration document into a User model.

    The database service can return a dictionary such as:

        {
            "id": "user_123",
            "name": "Vishal Singh",
            "email": "vishal@example.com",
            "role": "student",
            "is_active": True,
            "is_verified": False,
            "created_at": "...",
            "updated_at": "..."
        }

    The backend converts it into a validated User object.
    """

    if not isinstance(
        document,
        dict,
    ):
        raise ValueError(
            "User document must be a dictionary."
        )

    required_fields = {
        "id",
        "name",
        "email",
    }

    missing_fields = [
        field
        for field in required_fields
        if field not in document
    ]

    if missing_fields:

        raise ValueError(
            "User document is missing required fields: "
            + ", ".join(missing_fields)
        )

    return build_user(
        user_id=str(
            document["id"]
        ),
        name=str(
            document["name"]
        ),
        email=str(
            document["email"]
        ),
        phone_number=str(
            document.get(
        "phone_number",
        "",
    )
        ),
        role=str(
            document.get(
                "role",
                "student",
            )
        ),
        is_active=bool(
            document.get(
                "is_active",
                True,
            )
        ),
        is_verified=bool(
            document.get(
                "is_verified",
                False,
            )
        ),
        created_at=document.get(
            "created_at"
        ),
        updated_at=document.get(
            "updated_at"
        ),
    )


# ============================================================
# CONVERT USER TO PUBLIC DATA
# ============================================================

def user_to_public(
    user: User,
) -> UserPublic:
    """
    Convert a User object into the safe public representation.

    Password-related information is not present in User anyway,
    but keeping this conversion explicit prevents accidental
    exposure if the internal model evolves later.
    """

    return UserPublic(
        id=user.id,
        name=user.name,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ============================================================
# CONVERT USER TO DOCUMENT
# ============================================================

def user_to_document(
    user: UserAuthentication,
) -> Dict[str, Any]:
    """
    Convert an authenticated internal user into a
    database-service-friendly dictionary.

    This function does NOT perform database writes.

    The database integration layer decides how this dictionary
    is stored.
    """

    return {
        "id": user.id,
        "name": user.name,
        "email": str(
            user.email
        ),
        "phone_number": user.phone_number,
        "password_hash": user.password_hash,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


# ============================================================
# USER UPDATE DATA
# ============================================================

def get_user_update_data(
    update: UserUpdate,
) -> Dict[str, Any]:
    """
    Extract only the fields supplied in a UserUpdate request.

    This is useful for partial profile updates.
    """

    data = update.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "role" in data:
        data["role"] = normalize_user_role(
            data["role"]
        )

    return data


# ============================================================
# USER ACTIVE CHECK
# ============================================================

def is_user_active(
    user: User,
) -> bool:
    """
    Check whether a user is currently active.
    """

    return user.is_active


# ============================================================
# USER VERIFICATION CHECK
# ============================================================

def is_user_verified(
    user: User,
) -> bool:
    """
    Check whether a user has been verified.
    """

    return user.is_verified