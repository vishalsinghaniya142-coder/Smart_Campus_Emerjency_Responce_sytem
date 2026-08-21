from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.response import (
    error_response,
    server_error_response,
    validation_error_response,
)


# ============================================================
# ERROR IDENTIFIERS
# ============================================================

HTTP_ERROR = "HTTP_ERROR"
VALIDATION_ERROR = "VALIDATION_ERROR"
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


# ============================================================
# VALIDATION ERROR FORMATTER
# ============================================================

def format_validation_errors(
    errors: list,
) -> list:
    """
    Convert FastAPI/Pydantic validation errors into a simpler
    frontend-friendly format.

    Example output:

        [
            {
                "field": "email",
                "message": "Field required",
                "type": "missing"
            }
        ]
    """

    formatted_errors = []

    for error in errors:

        location = error.get(
            "loc",
            [],
        )

        message = error.get(
            "msg",
            "Invalid value.",
        )

        error_type = error.get(
            "type",
            "validation_error",
        )

        # ----------------------------------------------------
        # Remove technical prefixes such as:
        #
        # ("body", "email")
        #
        # and convert them into:
        #
        # "email"
        # ----------------------------------------------------

        field_parts = []

        for part in location:

            if part in {
                "body",
                "query",
                "path",
                "header",
                "cookie",
            }:
                continue

            field_parts.append(
                str(part)
            )

        if field_parts:

            field = ".".join(
                field_parts
            )

        else:

            field = "request"

        formatted_errors.append(
            {
                "field": field,
                "message": message,
                "type": error_type,
            }
        )

    return formatted_errors


# ============================================================
# HTTP EXCEPTION HANDLER
# ============================================================

async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle HTTPException errors.

    Examples:

        400 Bad Request
        401 Unauthorized
        403 Forbidden
        404 Not Found
        405 Method Not Allowed
        409 Conflict
        429 Too Many Requests
    """

    status_code = exc.status_code

    # --------------------------------------------------------
    # Determine an appropriate error identifier.
    # --------------------------------------------------------

    error_code = HTTP_ERROR

    if status_code == status.HTTP_400_BAD_REQUEST:
        error_code = "BAD_REQUEST"

    elif status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = "UNAUTHORIZED"

    elif status_code == status.HTTP_403_FORBIDDEN:
        error_code = "FORBIDDEN"

    elif status_code == status.HTTP_404_NOT_FOUND:
        error_code = "NOT_FOUND"

    elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        error_code = "METHOD_NOT_ALLOWED"

    elif status_code == status.HTTP_409_CONFLICT:
        error_code = "CONFLICT"

    elif status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        error_code = "UNPROCESSABLE_ENTITY"

    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        error_code = "TOO_MANY_REQUESTS"

    elif status_code >= 500:
        error_code = INTERNAL_SERVER_ERROR

    # --------------------------------------------------------
    # Extract exception detail.
    # --------------------------------------------------------

    detail = exc.detail

    if isinstance(detail, str):

        message = detail
        details = None

    else:

        message = "The request could not be completed."
        details = detail

    # --------------------------------------------------------
    # Build standardized response.
    # --------------------------------------------------------

    response_body = error_response(
        message=message,
        error=error_code,
        status_code=status_code,
        details=details,
    )

    # --------------------------------------------------------
    # Preserve WWW-Authenticate when required by JWT auth.
    # --------------------------------------------------------

    headers = {}

    if exc.headers:

        headers.update(
            exc.headers
        )

    return JSONResponse(
        status_code=status_code,
        content=response_body,
        headers=headers,
    )


# ============================================================
# REQUEST VALIDATION ERROR HANDLER
# ============================================================

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI request validation errors.

    These errors usually happen when:
        - required fields are missing
        - wrong data types are sent
        - invalid query parameters are used
        - invalid path parameters are supplied

    The frontend receives a clean list of validation errors.
    """

    formatted_errors = format_validation_errors(
        exc.errors()
    )

    response_body = validation_error_response(
        message="Request validation failed.",
        details=formatted_errors,
    )

    return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response_body,
    )


# ============================================================
# GENERAL EXCEPTION HANDLER
# ============================================================

async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application errors.

    IMPORTANT:

    We do not expose raw exception messages to the frontend.

    This prevents accidental exposure of:
        - internal paths
        - database details
        - secret configuration
        - stack traces
        - implementation details
    """

    response_body = server_error_response(
        message="An unexpected server error occurred.",
        details=None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_body,
    )


# ============================================================
# PYTHON VALUE ERROR HANDLER
# ============================================================

async def value_error_handler(
    request: Request,
    exc: ValueError,
) -> JSONResponse:
    """
    Handle ValueError exceptions.

    These can occur in validation/helper functions when
    converting or validating application data.
    """

    response_body = error_response(
        message=str(exc) or "Invalid value.",
        error="INVALID_VALUE",
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_body,
    )


# ============================================================
# TYPE ERROR HANDLER
# ============================================================

async def type_error_handler(
    request: Request,
    exc: TypeError,
) -> JSONResponse:
    """
    Handle unexpected type errors.

    The raw Python exception is not exposed to the frontend.
    """

    response_body = error_response(
        message="Invalid data type supplied.",
        error="INVALID_TYPE",
        status_code=status.HTTP_400_BAD_REQUEST,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response_body,
    )


# ============================================================
# REGISTER ERROR HANDLERS
# ============================================================

def register_exception_handlers(
    application: FastAPI,
) -> FastAPI:
    """
    Register all application-wide exception handlers.

    This function is called once when the FastAPI application
    is assembled.

    Flow:

        FastAPI application
                |
                v
        register_exception_handlers()
                |
        +-------+--------+----------------+
        |                |                |
        v                v                v
    HTTP errors     Validation       Unexpected errors
        |                |                |
        +-------+--------+----------------+
                |
                v
        standardized JSON response
    """

    # --------------------------------------------------------
    # HTTP exceptions
    # --------------------------------------------------------

    application.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )

    # --------------------------------------------------------
    # Request validation exceptions
    # --------------------------------------------------------

    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    # --------------------------------------------------------
    # ValueError
    # --------------------------------------------------------

    application.add_exception_handler(
        ValueError,
        value_error_handler,
    )

    # --------------------------------------------------------
    # TypeError
    # --------------------------------------------------------

    application.add_exception_handler(
        TypeError,
        type_error_handler,
    )

    # --------------------------------------------------------
    # Catch-all exception handler
    # --------------------------------------------------------

    application.add_exception_handler(
        Exception,
        general_exception_handler,
    )

    return application


# ============================================================
# ERROR RESPONSE BUILDER
# ============================================================

def build_http_error(
    status_code: int,
    message: str,
    error_code: str = HTTP_ERROR,
    details: Any = None,
) -> Dict[str, Any]:
    """
    Utility for building a standardized HTTP error payload.

    This does not raise an exception.

    It can be useful inside service/integration layers where
    an error needs to be converted into the project's common
    response structure.
    """

    return error_response(
        message=message,
        error=error_code,
        status_code=status_code,
        details=details,
    )