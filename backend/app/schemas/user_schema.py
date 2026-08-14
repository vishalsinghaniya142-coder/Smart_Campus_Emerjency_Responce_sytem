from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.utils.validators import (
    validate_email,
    validate_name,
    validate_user_role,
)


# ============================================================
# BASE USER SCHEMA
# ============================================================

class UserBase(BaseModel):
    """
    Common fields shared by user-related schemas.

    This schema contains only public/basic user information.
    Authentication secrets are intentionally excluded.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user.",
        examples=["Vishal Singh"],
    )

    email: EmailStr = Field(
        ...,
        description="User email address.",
        examples=["vishal@example.com"],
    )

    role: str = Field(
        default="student",
        max_length=30,
        description="Application role of the user.",
        examples=["student"],
    )

    @field_validator("name")
    @classmethod
    def validate_name_field(
        cls,
        value: str,
    ) -> str:
        """
        Normalize and validate the user's name.
        """

        return validate_name(
            value,
            field_name="Name",
        )

    @field_validator("email")
    @classmethod
    def validate_email_field(
        cls,
        value: EmailStr,
    ) -> EmailStr:
        """
        Normalize and validate the user's email.
        """

        normalized = validate_email(
            str(value)
        )

        return EmailStr(
            normalized
        )

    @field_validator("role")
    @classmethod
    def validate_role_field(
        cls,
        value: str,
    ) -> str:
        """
        Validate the user's application role.
        """

        return validate_user_role(
            value
        )


# ============================================================
# USER CREATE REQUEST
# ============================================================

class UserCreateRequest(UserBase):
    """
    Internal/API contract for creating a user.

    Authentication registration normally uses
    RegisterRequest from auth_schema.py.

    This schema is kept separate so future user-management
    operations can reuse a dedicated user contract.
    """

    pass


# ============================================================
# USER UPDATE REQUEST
# ============================================================

class UserUpdateRequest(BaseModel):
    """
    Request body for updating the current user's profile.

    Endpoint:

        PATCH /users/profile

    Only profile-editable fields are accepted here.

    Role changes are intentionally excluded because changing a
    user's privileges should not be possible through the normal
    profile endpoint.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated user name.",
        examples=["Vishal Singh"],
    )

    email: Optional[EmailStr] = Field(
        default=None,
        description="Updated email address.",
        examples=["newemail@example.com"],
    )

    @field_validator("name")
    @classmethod
    def validate_name_field(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Validate an optional updated name.
        """

        if value is None:
            return None

        return validate_name(
            value,
            field_name="Name",
        )

    @field_validator("email")
    @classmethod
    def validate_email_field(
        cls,
        value: Optional[EmailStr],
    ) -> Optional[EmailStr]:
        """
        Validate an optional updated email.
        """

        if value is None:
            return None

        normalized = validate_email(
            str(value)
        )

        return EmailStr(
            normalized
        )


# ============================================================
# USER PUBLIC RESPONSE
# ============================================================

class UserResponse(BaseModel):
    """
    Public user representation returned by the API.

    SECURITY:
        No password or password_hash field is present.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )

    id: str = Field(
        ...,
        description="Unique user ID.",
        examples=["user_123"],
    )

    name: str = Field(
        ...,
        description="User's full name.",
        examples=["Vishal Singh"],
    )

    email: EmailStr = Field(
        ...,
        description="User's email address.",
        examples=["vishal@example.com"],
    )

    role: str = Field(
        ...,
        description="User's application role.",
        examples=["student"],
    )

    is_active: bool = Field(
        default=True,
        description="Whether the account is active.",
    )

    is_verified: bool = Field(
        default=False,
        description="Whether the account is verified.",
    )

    created_at: datetime = Field(
        ...,
        description="UTC creation timestamp.",
    )

    updated_at: datetime = Field(
        ...,
        description="UTC last-update timestamp.",
    )


# ============================================================
# CURRENT USER RESPONSE
# ============================================================

class CurrentUserResponse(BaseModel):
    """
    Response contract for:

        GET /users/me

    This is intentionally smaller than the complete profile
    response.
    """

    id: str

    email: EmailStr

    role: str


# ============================================================
# USER PROFILE RESPONSE
# ============================================================

class UserProfileResponse(BaseModel):
    """
    Response contract for:

        GET /users/profile
    """

    id: str

    name: str

    email: EmailStr

    role: str

    is_active: bool

    is_verified: bool

    created_at: datetime

    updated_at: datetime


# ============================================================
# USER PROFILE UPDATE RESPONSE
# ============================================================

class UserProfileUpdateResponse(BaseModel):
    """
    Response contract after:

        PATCH /users/profile
    """

    id: str

    name: str

    email: EmailStr

    role: str

    is_active: bool

    is_verified: bool

    created_at: datetime

    updated_at: datetime


# ============================================================
# USER LIST ITEM
# ============================================================

class UserListItem(BaseModel):
    """
    Lightweight user representation for future list/admin
    endpoints.

    This is intentionally smaller than UserResponse.
    """

    id: str

    name: str

    email: EmailStr

    role: str

    is_active: bool

    is_verified: bool


# ============================================================
# USER LIST RESPONSE
# ============================================================

class UserListResponse(BaseModel):
    """
    Response contract for future user-list endpoints.

    Example:

        {
            "users": [...],
            "total": 20
        }
    """

    users: list[UserListItem] = Field(
        default_factory=list
    )

    total: int = Field(
        default=0,
        ge=0,
    )


# ============================================================
# USER STATUS RESPONSE
# ============================================================

class UserStatusResponse(BaseModel):
    """
    Lightweight response for account status.
    """

    id: str

    is_active: bool

    is_verified: bool


# ============================================================
# USER PROFILE DATA CONVERTER
# ============================================================

def build_user_response(
    user: object,
) -> UserResponse:
    """
    Convert a backend User model/object into the public
    UserResponse schema.

    This function ensures that only approved public fields are
    exposed.
    """

    return UserResponse.model_validate(
        user
    )


# ============================================================
# CURRENT USER DATA CONVERTER
# ============================================================

def build_current_user_response(
    user_id: str,
    email: str,
    role: str,
) -> CurrentUserResponse:
    """
    Build the lightweight current-user response.
    """

    return CurrentUserResponse(
        id=str(user_id),
        email=EmailStr(
            validate_email(
                email
            )
        ),
        role=validate_user_role(
            role
        ),
    )


# ============================================================
# PROFILE UPDATE DATA EXTRACTOR
# ============================================================

def extract_profile_update_data(
    payload: UserUpdateRequest,
) -> dict:
    """
    Extract only fields actually supplied by the client.

    This is useful for PATCH semantics.

    Example:

        {
            "name": "Vishal Singh"
        }

    becomes:

        {
            "name": "Vishal Singh"
        }

    while unspecified fields remain untouched.
    """

    return payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )


# ============================================================
# CHECK WHETHER UPDATE IS EMPTY
# ============================================================

def has_profile_updates(
    payload: UserUpdateRequest,
) -> bool:
    """
    Check whether the client actually supplied at least one
    profile field.
    """

    data = extract_profile_update_data(
        payload
    )

    return bool(data)
