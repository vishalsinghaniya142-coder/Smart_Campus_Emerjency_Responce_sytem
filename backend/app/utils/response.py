from typing import Any, Dict, List, Optional


# ============================================================
# RESPONSE STATUS VALUES
# ============================================================

SUCCESS_STATUS = "success"
ERROR_STATUS = "error"


# ============================================================
# SUCCESS RESPONSE
# ============================================================

def success_response(
    message: str = "Request completed successfully.",
    data: Any = None,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized successful API response.

    Example:

        {
            "success": True,
            "message": "Profile fetched successfully.",
            "data": {...},
            "meta": None
        }

    Parameters
    ----------
    message:
        Human-readable response message.

    data:
        Actual response payload.

    status_code:
        HTTP status code associated with the response.

    meta:
        Optional metadata such as pagination information.
    """

    response = {
        "success": True,
        "status": SUCCESS_STATUS,
        "message": message,
        "data": data,
    }

    if meta is not None:
        response["meta"] = meta

    return response


# ============================================================
# ERROR RESPONSE
# ============================================================

def error_response(
    message: str = "Request could not be completed.",
    error: Any = None,
    status_code: int = 400,
    details: Any = None,
) -> Dict[str, Any]:
    """
    Create a standardized error API response.

    Example:

        {
            "success": False,
            "status": "error",
            "message": "Invalid request.",
            "error": "...",
            "details": ...
        }

    Parameters
    ----------
    message:
        Main error message.

    error:
        Short error identifier or technical error.

    status_code:
        HTTP status code associated with the error.

    details:
        Optional validation or debugging details.
    """

    response = {
        "success": False,
        "status": ERROR_STATUS,
        "message": message,
        "error": error,
    }

    if details is not None:
        response["details"] = details

    return response


# ============================================================
# CREATED RESPONSE
# ============================================================

def created_response(
    data: Any = None,
    message: str = "Resource created successfully.",
) -> Dict[str, Any]:
    """
    Standard response for a successfully created resource.

    Normally used with HTTP 201.
    """

    return success_response(
        message=message,
        data=data,
        status_code=201,
    )


# ============================================================
# UPDATED RESPONSE
# ============================================================

def updated_response(
    data: Any = None,
    message: str = "Resource updated successfully.",
) -> Dict[str, Any]:
    """
    Standard response for a successfully updated resource.
    """

    return success_response(
        message=message,
        data=data,
        status_code=200,
    )


# ============================================================
# DELETED RESPONSE
# ============================================================

def deleted_response(
    data: Any = None,
    message: str = "Resource deleted successfully.",
) -> Dict[str, Any]:
    """
    Standard response for a successfully deleted resource.
    """

    return success_response(
        message=message,
        data=data,
        status_code=200,
    )


# ============================================================
# NOT FOUND RESPONSE
# ============================================================

def not_found_response(
    resource: str = "Resource",
    resource_id: Any = None,
) -> Dict[str, Any]:
    """
    Standard response when a requested resource does not exist.
    """

    if resource_id is not None:

        message = (
            f"{resource} with ID "
            f"'{resource_id}' was not found."
        )

    else:

        message = (
            f"{resource} was not found."
        )

    return error_response(
        message=message,
        error="NOT_FOUND",
        status_code=404,
    )


# ============================================================
# UNAUTHORIZED RESPONSE
# ============================================================

def unauthorized_response(
    message: str = "Authentication is required.",
) -> Dict[str, Any]:
    """
    Standard response for authentication failures.
    """

    return error_response(
        message=message,
        error="UNAUTHORIZED",
        status_code=401,
    )


# ============================================================
# FORBIDDEN RESPONSE
# ============================================================

def forbidden_response(
    message: str = "You do not have permission to perform this action.",
) -> Dict[str, Any]:
    """
    Standard response for authorization failures.
    """

    return error_response(
        message=message,
        error="FORBIDDEN",
        status_code=403,
    )


# ============================================================
# VALIDATION ERROR RESPONSE
# ============================================================

def validation_error_response(
    message: str = "Validation failed.",
    details: Any = None,
) -> Dict[str, Any]:
    """
    Standard response for invalid request data.
    """

    return error_response(
        message=message,
        error="VALIDATION_ERROR",
        status_code=422,
        details=details,
    )


# ============================================================
# CONFLICT RESPONSE
# ============================================================

def conflict_response(
    message: str = "The requested operation conflicts with existing data.",
    details: Any = None,
) -> Dict[str, Any]:
    """
    Standard response for resource conflicts.

    Examples:
        - Email already registered
        - Duplicate incident
        - Duplicate resource
    """

    return error_response(
        message=message,
        error="CONFLICT",
        status_code=409,
        details=details,
    )


# ============================================================
# SERVER ERROR RESPONSE
# ============================================================

def server_error_response(
    message: str = "An internal server error occurred.",
    details: Any = None,
) -> Dict[str, Any]:
    """
    Standard response for unexpected server-side errors.
    """

    return error_response(
        message=message,
        error="INTERNAL_SERVER_ERROR",
        status_code=500,
        details=details,
    )


# ============================================================
# SERVICE UNAVAILABLE RESPONSE
# ============================================================

def service_unavailable_response(
    service: str = "External service",
    details: Any = None,
) -> Dict[str, Any]:
    """
    Standard response when an external/internal dependency
    is temporarily unavailable.

    This can later be useful for:
        - AI service
        - Firebase
        - Maps
        - notification service
    """

    return error_response(
        message=f"{service} is currently unavailable.",
        error="SERVICE_UNAVAILABLE",
        status_code=503,
        details=details,
    )


# ============================================================
# PAGINATION META
# ============================================================

def pagination_meta(
    page: int,
    page_size: int,
    total_items: int,
) -> Dict[str, Any]:
    """
    Create standardized pagination metadata.
    """

    if page <= 0:
        page = 1

    if page_size <= 0:
        page_size = 1

    if total_items < 0:
        total_items = 0

    total_pages = (
        (total_items + page_size - 1)
        // page_size
    )

    has_next = page < total_pages
    has_previous = page > 1

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous,
    }


# ============================================================
# PAGINATED SUCCESS RESPONSE
# ============================================================

def paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Data fetched successfully.",
) -> Dict[str, Any]:
    """
    Create a standardized paginated response.

    Example:

        {
            "success": True,
            "status": "success",
            "message": "...",
            "data": [...],
            "meta": {
                "page": 1,
                "page_size": 20,
                "total_items": 100,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }
    """

    meta = pagination_meta(
        page=page,
        page_size=page_size,
        total_items=total_items,
    )

    return success_response(
        message=message,
        data=data,
        meta=meta,
    )


# ============================================================
# EMPTY SUCCESS RESPONSE
# ============================================================

def empty_success_response(
    message: str = "Request completed successfully.",
) -> Dict[str, Any]:
    """
    Standard successful response without a data payload.
    """

    return success_response(
        message=message,
        data=None,
    )


# ============================================================
# LIST SUCCESS RESPONSE
# ============================================================

def list_response(
    data: List[Any],
    message: str = "Data fetched successfully.",
) -> Dict[str, Any]:
    """
    Standard response for a list endpoint.
    """

    return success_response(
        message=message,
        data=data,
    )


# ============================================================
# SINGLE RESOURCE RESPONSE
# ============================================================

def resource_response(
    data: Any,
    message: str = "Resource fetched successfully.",
) -> Dict[str, Any]:
    """
    Standard response for a single resource.
    """

    return success_response(
        message=message,
        data=data,
    )


# ============================================================
# AUTHENTICATION RESPONSE
# ============================================================

def authentication_response(
    user: Any,
    access_token: str,
    message: str = "Authentication successful.",
    token_type: str = "bearer",
) -> Dict[str, Any]:
    """
    Standard response returned after successful login.

    Example:

        {
            "success": True,
            "status": "success",
            "message": "Login successful.",
            "data": {
                "user": {...},
                "access_token": "...",
                "token_type": "bearer"
            }
        }

    This will later connect naturally with the JWT handler.
    """

    return success_response(
        message=message,
        data={
            "user": user,
            "access_token": access_token,
            "token_type": token_type,
        },
    )


# ============================================================
# INCIDENT RESPONSE
# ============================================================

def incident_response(
    incident: Any,
    message: str = "Incident processed successfully.",
) -> Dict[str, Any]:
    """
    Standard response for incident operations.

    Kept as a dedicated helper so the response contract can
    evolve later without changing every incident route.
    """

    return success_response(
        message=message,
        data=incident,
    )


# ============================================================
# SOS RESPONSE
# ============================================================

def sos_response(
    sos: Any,
    message: str = "SOS request processed successfully.",
) -> Dict[str, Any]:
    """
    Standard response for SOS operations.
    """

    return success_response(
        message=message,
        data=sos,
    )


# ============================================================
# ALERT RESPONSE
# ============================================================

def alert_response(
    alert: Any,
    message: str = "Alert processed successfully.",
) -> Dict[str, Any]:
    """
    Standard response for emergency alert operations.
    """

    return success_response(
        message=message,
        data=alert,
    )


# ============================================================
# SHELTER RESPONSE
# ============================================================

def shelter_response(
    shelter: Any,
    message: str = "Shelter information fetched successfully.",
) -> Dict[str, Any]:
    """
    Standard response for shelter operations.
    """

    return success_response(
        message=message,
        data=shelter,
    )


# ============================================================
# AI RESPONSE
# ============================================================

def ai_response(
    data: Any,
    message: str = "AI request processed successfully.",
) -> Dict[str, Any]:
    """
    Standard response for AI-related operations.

    This can be used by:
        - prediction
        - chatbot
        - image analysis

    The actual AI logic remains outside this response helper.
    """

    return success_response(
        message=message,
        data=data,
    )


# ============================================================
# RESPONSE DATA NORMALIZATION
# ============================================================

def normalize_data(
    data: Any,
) -> Any:
    """
    Basic response-data normalization helper.

    This function intentionally does not perform database
    serialization. Pydantic schemas / model serializers should
    handle complex objects.

    It only handles a few common Python structures.
    """

    if data is None:
        return None

    if isinstance(data, dict):
        return {
            str(key): normalize_data(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            normalize_data(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return [
            normalize_data(item)
            for item in data
        ]

    if isinstance(data, (
        str,
        int,
        float,
        bool,
    )):
        return data

    return data


# ============================================================
# FINAL RESPONSE BUILDER
# ============================================================

def build_response(
    success: bool,
    message: str,
    data: Any = None,
    error: Any = None,
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generic response builder.

    This function is useful when a service needs to construct
    a response dynamically.

    Most routes should prefer the more specific helpers above
    because they make the intended response type clearer.
    """

    if success:

        return success_response(
            message=message,
            data=normalize_data(data),
            status_code=status_code,
            meta=meta,
        )

    return error_response(
        message=message,
        error=error,
        status_code=status_code,
        details=meta,
    )