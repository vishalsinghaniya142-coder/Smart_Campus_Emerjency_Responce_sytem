import re
from datetime import date, datetime
from typing import Any, Optional


# ============================================================
# COMMON CONSTANTS
# ============================================================

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 100

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000

MAX_EMAIL_LENGTH = 254


# ============================================================
# EMAIL VALIDATION
# ============================================================

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@"
    r"[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_email(
    email: str,
) -> str:
    """
    Validate and normalize an email address.

    Returns the normalized lowercase email.

    Raises:
        ValueError: if the email is invalid.
    """

    if not isinstance(email, str):
        raise ValueError(
            "Email must be a string."
        )

    email = email.strip().lower()

    if not email:
        raise ValueError(
            "Email is required."
        )

    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(
            "Email address is too long."
        )

    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError(
            "Please provide a valid email address."
        )

    return email


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(
    password: str,
) -> str:
    """
    Validate a user password.

    Rules:
        - Must be a string
        - Minimum 8 characters
        - Maximum 128 characters
        - Must contain at least one letter
        - Must contain at least one number

    The password itself is returned unchanged because
    validation should happen before hashing.
    """

    if not isinstance(password, str):
        raise ValueError(
            "Password must be a string."
        )

    if not password:
        raise ValueError(
            "Password is required."
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password cannot contain more than "
            f"{MAX_PASSWORD_LENGTH} characters."
        )

    if not re.search(r"[A-Za-z]", password):
        raise ValueError(
            "Password must contain at least one letter."
        )

    if not re.search(r"\d", password):
        raise ValueError(
            "Password must contain at least one number."
        )

    return password


# ============================================================
# NAME VALIDATION
# ============================================================

def validate_name(
    name: str,
    field_name: str = "Name",
) -> str:
    """
    Validate a person's name.

    Leading/trailing whitespace is removed and repeated
    internal whitespace is normalized.
    """

    if not isinstance(name, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    name = " ".join(
        name.strip().split()
    )

    if not name:
        raise ValueError(
            f"{field_name} is required."
        )

    if len(name) < MIN_NAME_LENGTH:
        raise ValueError(
            f"{field_name} must contain at least "
            f"{MIN_NAME_LENGTH} characters."
        )

    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(
            f"{field_name} cannot contain more than "
            f"{MAX_NAME_LENGTH} characters."
        )

    # Allow letters, spaces, apostrophes and hyphens.
    if not re.fullmatch(
        r"[A-Za-zÀ-ÖØ-öø-ÿ' -]+",
        name,
    ):
        raise ValueError(
            f"{field_name} contains invalid characters."
        )

    return name


# ============================================================
# TEXT VALIDATION
# ============================================================

def validate_text(
    value: str,
    field_name: str,
    min_length: int = 1,
    max_length: int = 500,
    required: bool = True,
) -> Optional[str]:
    """
    Generic text validator.

    Useful for:
        titles
        descriptions
        locations
        names
        messages
        other textual fields
    """

    if value is None:

        if required:
            raise ValueError(
                f"{field_name} is required."
            )

        return None

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    value = value.strip()

    if not value:

        if required:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return None

    if len(value) < min_length:
        raise ValueError(
            f"{field_name} must contain at least "
            f"{min_length} characters."
        )

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot contain more than "
            f"{max_length} characters."
        )

    return value


# ============================================================
# TITLE VALIDATION
# ============================================================

def validate_title(
    title: str,
    field_name: str = "Title",
) -> str:
    """
    Validate a title field.
    """

    return validate_text(
        title,
        field_name=field_name,
        min_length=1,
        max_length=MAX_TITLE_LENGTH,
        required=True,
    )


# ============================================================
# DESCRIPTION VALIDATION
# ============================================================

def validate_description(
    description: str,
    field_name: str = "Description",
    required: bool = False,
) -> Optional[str]:
    """
    Validate a description field.
    """

    return validate_text(
        description,
        field_name=field_name,
        min_length=1,
        max_length=MAX_DESCRIPTION_LENGTH,
        required=required,
    )


# ============================================================
# INTEGER VALIDATION
# ============================================================

def validate_integer(
    value: Any,
    field_name: str,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    """
    Validate an integer value.
    """

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be an integer."
        )

    try:
        number = int(value)

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            f"{field_name} must be an integer."
        ) from exc

    if minimum is not None and number < minimum:
        raise ValueError(
            f"{field_name} must be at least {minimum}."
        )

    if maximum is not None and number > maximum:
        raise ValueError(
            f"{field_name} cannot be greater than {maximum}."
        )

    return number


# ============================================================
# FLOAT VALIDATION
# ============================================================

def validate_float(
    value: Any,
    field_name: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> float:
    """
    Validate a floating-point value.
    """

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            f"{field_name} must be a valid number."
        ) from exc

    if minimum is not None and number < minimum:
        raise ValueError(
            f"{field_name} must be at least {minimum}."
        )

    if maximum is not None and number > maximum:
        raise ValueError(
            f"{field_name} cannot be greater than {maximum}."
        )

    return number


# ============================================================
# LATITUDE VALIDATION
# ============================================================

def validate_latitude(
    latitude: Any,
) -> float:
    """
    Validate geographic latitude.

    Valid range:
        -90 to +90
    """

    return validate_float(
        latitude,
        field_name="Latitude",
        minimum=-90.0,
        maximum=90.0,
    )


# ============================================================
# LONGITUDE VALIDATION
# ============================================================

def validate_longitude(
    longitude: Any,
) -> float:
    """
    Validate geographic longitude.

    Valid range:
        -180 to +180
    """

    return validate_float(
        longitude,
        field_name="Longitude",
        minimum=-180.0,
        maximum=180.0,
    )


# ============================================================
# COORDINATE VALIDATION
# ============================================================

def validate_coordinates(
    latitude: Any,
    longitude: Any,
) -> tuple[float, float]:
    """
    Validate latitude and longitude together.

    Returns:
        (latitude, longitude)
    """

    validated_latitude = validate_latitude(
        latitude
    )

    validated_longitude = validate_longitude(
        longitude
    )

    return (
        validated_latitude,
        validated_longitude,
    )


# ============================================================
# ENUM / CHOICE VALIDATION
# ============================================================

def validate_choice(
    value: str,
    field_name: str,
    allowed_values: set[str],
) -> str:
    """
    Validate that a value belongs to an allowed set.

    Example:

        validate_choice(
            "high",
            "Priority",
            {"low", "medium", "high"}
        )
    """

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a string."
        )

    value = value.strip().lower()

    if value not in allowed_values:
        choices = ", ".join(
            sorted(allowed_values)
        )

        raise ValueError(
            f"Invalid {field_name.lower()}. "
            f"Allowed values: {choices}."
        )

    return value


# ============================================================
# INCIDENT TYPE VALIDATION
# ============================================================

ALLOWED_INCIDENT_TYPES = {
    "fire",
    "medical",
    "accident",
    "violence",
    "natural_disaster",
    "security",
    "other",
}


def validate_incident_type(
    incident_type: str,
) -> str:
    """
    Validate an emergency incident type.
    """

    return validate_choice(
        incident_type,
        "Incident type",
        ALLOWED_INCIDENT_TYPES,
    )


# ============================================================
# INCIDENT STATUS VALIDATION
# ============================================================

ALLOWED_INCIDENT_STATUSES = {
    "reported",
    "investigating",
    "responding",
    "resolved",
    "cancelled",
}


def validate_incident_status(
    status: str,
) -> str:
    """
    Validate an emergency incident status.
    """

    return validate_choice(
        status,
        "Incident status",
        ALLOWED_INCIDENT_STATUSES,
    )


# ============================================================
# ALERT SEVERITY VALIDATION
# ============================================================

ALLOWED_ALERT_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


def validate_alert_severity(
    severity: str,
) -> str:
    """
    Validate emergency alert severity.
    """

    return validate_choice(
        severity,
        "Alert severity",
        ALLOWED_ALERT_SEVERITIES,
    )


# ============================================================
# SOS STATUS VALIDATION
# ============================================================

ALLOWED_SOS_STATUSES = {
    "active",
    "acknowledged",
    "responding",
    "resolved",
    "cancelled",
}


def validate_sos_status(
    status: str,
) -> str:
    """
    Validate SOS status.
    """

    return validate_choice(
        status,
        "SOS status",
        ALLOWED_SOS_STATUSES,
    )


# ============================================================
# USER ROLE VALIDATION
# ============================================================

ALLOWED_USER_ROLES = {
    "user",
    "student",
    "staff",
    "admin",
}


def validate_user_role(
    role: str,
) -> str:
    """
    Validate application user role.
    """

    return validate_choice(
        role,
        "User role",
        ALLOWED_USER_ROLES,
    )


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date(
    value: Any,
    field_name: str = "Date",
) -> date:
    """
    Validate a date.

    Accepted:
        datetime.date
        datetime.datetime
        ISO date string: YYYY-MM-DD
    """

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a valid date."
        )

    try:
        return date.fromisoformat(
            value.strip()
        )

    except ValueError as exc:

        raise ValueError(
            f"{field_name} must use YYYY-MM-DD format."
        ) from exc


# ============================================================
# DATETIME VALIDATION
# ============================================================

def validate_datetime(
    value: Any,
    field_name: str = "Date and time",
) -> datetime:
    """
    Validate an ISO-compatible datetime.
    """

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a valid datetime."
        )

    try:

        parsed = datetime.fromisoformat(
            value.strip()
        )

    except ValueError as exc:

        raise ValueError(
            f"{field_name} must be a valid ISO datetime."
        ) from exc

    return parsed


# ============================================================
# UUID-LIKE / ID VALIDATION
# ============================================================

def validate_identifier(
    value: Any,
    field_name: str = "ID",
) -> str:
    """
    Validate a generic resource identifier.

    We intentionally do not force UUID format because the
    final database layer may use:
        UUID
        Firebase document ID
        another generated identifier
    """

    if value is None:
        raise ValueError(
            f"{field_name} is required."
        )

    identifier = str(value).strip()

    if not identifier:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    if len(identifier) > 200:
        raise ValueError(
            f"{field_name} is too long."
        )

    return identifier


# ============================================================
# FILE NAME VALIDATION
# ============================================================

def validate_filename(
    filename: str,
) -> str:
    """
    Validate an uploaded filename.

    This validation is intentionally conservative.

    It does not decide whether a file type is safe. Actual
    content-type and file-size checks should also happen in
    the image-analysis upload flow.
    """

    if not isinstance(filename, str):
        raise ValueError(
            "Filename must be a string."
        )

    filename = filename.strip()

    if not filename:
        raise ValueError(
            "Filename is required."
        )

    if len(filename) > 255:
        raise ValueError(
            "Filename is too long."
        )

    if "\x00" in filename:
        raise ValueError(
            "Filename contains an invalid character."
        )

    # Prevent basic path traversal.
    if ".." in filename:
        raise ValueError(
            "Filename contains an invalid path sequence."
        )

    if "/" in filename or "\\" in filename:
        raise ValueError(
            "Filename must not contain path separators."
        )

    return filename


# ============================================================
# IMAGE CONTENT TYPE VALIDATION
# ============================================================

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def validate_image_content_type(
    content_type: str,
) -> str:
    """
    Validate the MIME type of an uploaded image.
    """

    if not isinstance(content_type, str):
        raise ValueError(
            "Image content type must be a string."
        )

    content_type = (
        content_type
        .strip()
        .lower()
    )

    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        allowed = ", ".join(
            sorted(ALLOWED_IMAGE_CONTENT_TYPES)
        )

        raise ValueError(
            f"Unsupported image type. "
            f"Allowed types: {allowed}."
        )

    return content_type


# ============================================================
# SEARCH QUERY VALIDATION
# ============================================================

def validate_search_query(
    query: Optional[str],
) -> Optional[str]:
    """
    Validate an optional search query.
    """

    if query is None:
        return None

    if not isinstance(query, str):
        raise ValueError(
            "Search query must be a string."
        )

    query = query.strip()

    if not query:
        return None

    if len(query) > 200:
        raise ValueError(
            "Search query cannot exceed 200 characters."
        )

    return query


# ============================================================
# PAGINATION VALIDATION
# ============================================================

def validate_pagination(
    page: Any = 1,
    page_size: Any = 20,
    max_page_size: int = 100,
) -> tuple[int, int]:
    """
    Validate pagination values.

    Returns:
        (page, page_size)
    """

    validated_page = validate_integer(
        page,
        field_name="Page",
        minimum=1,
    )

    validated_page_size = validate_integer(
        page_size,
        field_name="Page size",
        minimum=1,
        maximum=max_page_size,
    )

    return (
        validated_page,
        validated_page_size,
    )


# ============================================================
# EMERGENCY MESSAGE VALIDATION
# ============================================================

def validate_emergency_message(
    message: str,
) -> str:
    """
    Validate an emergency message.

    This can be used by:
        SOS
        chatbot
        incident reporting
        emergency alerts
    """

    return validate_text(
        message,
        field_name="Emergency message",
        min_length=1,
        max_length=5000,
        required=True,
    )


# ============================================================
# SANITIZE SIMPLE TEXT
# ============================================================

def sanitize_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Perform basic text normalization.

    This function is NOT an HTML sanitizer and should not be
    treated as one.

    It only:
        - converts whitespace
        - removes surrounding whitespace
        - returns None for None input
    """

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(
            "Value must be a string."
        )

    return " ".join(
        value.strip().split()
    )


# ============================================================
# VALIDATE BOOLEAN
# ============================================================

def validate_boolean(
    value: Any,
    field_name: str,
) -> bool:
    """
    Validate a boolean value.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):

        normalized = (
            value.strip()
            .lower()
        )

        if normalized in {
            "true",
            "1",
            "yes",
            "on",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "off",
        }:
            return False

    raise ValueError(
        f"{field_name} must be a boolean."
    )