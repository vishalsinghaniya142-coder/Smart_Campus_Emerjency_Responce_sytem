from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.validators import (
    validate_name,
    validate_password,
)


# ============================================================
# BASE AUTH SCHEMA
# ============================================================

class AuthBase(BaseModel):
    """
    Common authentication-related fields.

    This base schema is intentionally small so that registration
    and login can have their own specific contracts.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )


# ============================================================
# REGISTER REQUEST
# ============================================================

class RegisterRequest(AuthBase):
    """
    Request body for:

        POST /auth/register

    Expected JSON:

        {
            "name": "Vishal Singh",
            "email": "vishal@example.com",
            "password": "password123"
        }
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user.",
        examples=["Vishal Singh"],
    )

    email: EmailStr = Field(
        ...,
        description="User's email address.",
        examples=["vishal@example.com"],
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password.",
        examples=["password123"],
    )

    role: Optional[str] = Field(
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
        Validate and normalize the user's name.
        """

        return validate_name(
            value,
            field_name="Name",
        )

    @field_validator("password")
    @classmethod
    def validate_password_field(
        cls,
        value: str,
    ) -> str:
        """
        Validate password requirements.
        """

        return validate_password(
            value
        )

    @field_validator("role")
    @classmethod
    def validate_role_field(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        """
        Normalize the role.

        The final allowed role validation can also be applied
        by the service/model layer.
        """

        if value is None:
            return "student"

        normalized = value.strip().lower()

        if not normalized:
            return "student"

        return normalized


# ============================================================
# LOGIN REQUEST
# ============================================================

class LoginRequest(AuthBase):
    """
    Request body for:

        POST /auth/login

    Expected JSON:

        {
            "email": "vishal@example.com",
            "password": "password123"
        }
    """

    email: EmailStr = Field(
        ...,
        description="Registered user email address.",
        examples=["vishal@example.com"],
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User's password.",
        examples=["password123"],
    )


# ============================================================
# USER AUTH RESPONSE
# ============================================================

class AuthUserResponse(BaseModel):
    """
    Public representation of an authenticated user.

    IMPORTANT:
        Password or password hash must NEVER be returned here.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = Field(
        ...,
        description="Unique user identifier.",
        examples=["user_123"],
    )

    name: str = Field(
        ...,
        description="User's display name.",
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


# ============================================================
# AUTH TOKEN RESPONSE
# ============================================================

class TokenResponse(BaseModel):
    """
    JWT token information returned after successful login.
    """

    access_token: str = Field(
        ...,
        description="JWT access token.",
    )

    token_type: str = Field(
        default="bearer",
        description="Authentication token type.",
        examples=["bearer"],
    )


# ============================================================
# LOGIN RESPONSE DATA
# ============================================================

class LoginResponseData(BaseModel):
    """
    Data returned by a successful login.

    Structure:

        {
            "user": {...},
            "access_token": "...",
            "token_type": "bearer"
        }
    """

    user: AuthUserResponse

    access_token: str = Field(
        ...,
        description="JWT access token.",
    )

    token_type: str = Field(
        default="bearer",
        description="Authentication token type.",
    )


# ============================================================
# REGISTER RESPONSE DATA
# ============================================================

class RegisterResponseData(BaseModel):
    """
    Data returned after successful registration.

    We intentionally do not return a password or password hash.
    """

    user: AuthUserResponse


# ============================================================
# GENERIC AUTH MESSAGE RESPONSE
# ============================================================

class AuthMessageResponse(BaseModel):
    """
    Generic authentication response containing a message.
    """

    success: bool = True

    status: str = "success"

    message: str


# ============================================================
# COMPLETE LOGIN API RESPONSE
# ============================================================

class LoginResponse(BaseModel):
    """
    Complete response contract for:

        POST /auth/login
    """

    success: bool = True

    status: str = "success"

    message: str = "Login successful."

    data: LoginResponseData


# ============================================================
# COMPLETE REGISTER API RESPONSE
# ============================================================

class RegisterResponse(BaseModel):
    """
    Complete response contract for:

        POST /auth/register
    """

    success: bool = True

    status: str = "success"

    message: str = "User registered successfully."

    data: RegisterResponseData