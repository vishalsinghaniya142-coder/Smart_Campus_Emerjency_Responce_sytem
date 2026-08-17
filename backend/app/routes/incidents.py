from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.dependencies import get_current_user

from app.models.incident import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)

from app.schemas.incident_schema import (
    IncidentCreateRequest,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdateRequest,
    build_incident_list_response,
    build_incident_response,
)

from app.services.incident_service import (
    create_incident,
    delete_incident,
    get_incident,
    list_incidents,
    update_incident,
)

from app.utils.response import (
    created_response,
    deleted_response,
    resource_response,
    updated_response,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# CREATE INCIDENT
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def report_incident(
    payload: IncidentCreateRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Report a new emergency incident.

    Endpoint
    --------
    POST /incidents

    Authentication
    --------------
    Required.

    Request
    -------
    The frontend sends incident information.

    reporter_id is NOT accepted from the frontend.

    It comes from the authenticated JWT.

    Flow
    ----

        Frontend
            |
            v
        POST /incidents
            |
            v
        get_current_user()
            |
            v
        reporter_id
            |
            v
        IncidentCreateRequest
            |
            v
        incident_service.create_incident()
            |
            +-----------> AI Service
            |
            +-----------> Database
            |
            v
        IncidentResponse
            |
            v
        Frontend
    """

    # --------------------------------------------------------
    # Get authenticated user ID
    # --------------------------------------------------------

    reporter_id = current_user.get(
        "id"
    )

    if not reporter_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Create incident through service layer
    # --------------------------------------------------------

    try:

        incident = await create_incident(
            payload=payload,
            reporter_id=reporter_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create incident.",
        ) from exc

    # --------------------------------------------------------
    # Convert model to API response
    # --------------------------------------------------------

    response_data = build_incident_response(
        incident
    )

    return created_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Incident reported successfully.",
    )


# ============================================================
# LIST INCIDENTS
# ============================================================

@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def get_incidents(
    incident_type: Optional[
        IncidentType
    ] = Query(
        default=None,
        description="Filter by incident type.",
    ),
    severity: Optional[
        IncidentSeverity
    ] = Query(
        default=None,
        description="Filter by severity.",
    ),
    incident_status: Optional[
        IncidentStatus
    ] = Query(
        default=None,
        alias="status",
        description="Filter by incident status.",
    ),
    reporter_id: Optional[
        str
    ] = Query(
        default=None,
        max_length=200,
        description="Filter by reporter ID.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of incidents.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of incidents to skip.",
    ),
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Get emergency incidents.

    Endpoint
    --------
    GET /incidents

    Authentication
    --------------
    Required.

    Supported query parameters:

        incident_type
        severity
        status
        reporter_id
        limit
        offset

    Example:

        GET /incidents?severity=critical&limit=20

    The authenticated user can request incidents through the
    service layer.

    Authorization/business rules remain inside the service
    layer rather than being duplicated here.
    """

    # --------------------------------------------------------
    # Ensure authentication context exists
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Fetch incidents
    # --------------------------------------------------------

    try:

        incidents = await list_incidents(
            incident_type=incident_type,
            severity=severity,
            status=incident_status,
            reporter_id=reporter_id,
            limit=limit,
            offset=offset,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch incidents.",
        ) from exc

    # --------------------------------------------------------
    # Build list response
    # --------------------------------------------------------

    response_data = build_incident_list_response(
        incidents
    )

    return resource_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Incidents fetched successfully.",
    )


# ============================================================
# GET INCIDENT BY ID
# ============================================================

@router.get(
    "/{incident_id}",
    status_code=status.HTTP_200_OK,
)
async def get_incident_by_id(
    incident_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Get a single incident by ID.

    Endpoint
    --------
    GET /incidents/{incident_id}

    Authentication
    --------------
    Required.

    Example:

        GET /incidents/inc_123456
    """

    # --------------------------------------------------------
    # Validate authenticated user
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Validate incident ID
    # --------------------------------------------------------

    if not incident_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident ID cannot be empty.",
        )

    # --------------------------------------------------------
    # Fetch incident
    # --------------------------------------------------------

    try:

        incident = await get_incident(
            incident_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch incident.",
        ) from exc

    # --------------------------------------------------------
    # Incident not found
    # --------------------------------------------------------

    if incident is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    # --------------------------------------------------------
    # Convert to response schema
    # --------------------------------------------------------

    response_data = build_incident_response(
        incident
    )

    return resource_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Incident fetched successfully.",
    )


# ============================================================
# UPDATE INCIDENT
# ============================================================

@router.patch(
    "/{incident_id}",
    status_code=status.HTTP_200_OK,
)
async def update_incident_route(
    incident_id: str,
    payload: IncidentUpdateRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Update an incident.

    Endpoint
    --------
    PATCH /incidents/{incident_id}

    Authentication
    --------------
    Required.

    Ownership authorization is handled by the service layer.
    """

    # --------------------------------------------------------
    # Get authenticated user
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Validate incident ID
    # --------------------------------------------------------

    if not incident_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident ID cannot be empty.",
        )

    # --------------------------------------------------------
    # Update through service
    # --------------------------------------------------------

    try:

        incident = await update_incident(
            incident_id=incident_id,
            payload=payload,
            requester_id=user_id,
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update incident.",
        ) from exc

    # --------------------------------------------------------
    # Incident not found
    # --------------------------------------------------------

    if incident is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    response_data = build_incident_response(
        incident
    )

    return updated_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Incident updated successfully.",
    )


# ============================================================
# DELETE INCIDENT
# ============================================================

@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_incident_route(
    incident_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Delete an incident.

    Endpoint
    --------
    DELETE /incidents/{incident_id}

    Authentication
    --------------
    Required.

    The service layer verifies ownership and whether the
    incident is eligible for deletion.
    """

    # --------------------------------------------------------
    # Authenticated user
    # --------------------------------------------------------

    user_id = current_user.get(
        "id"
    )

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Validate ID
    # --------------------------------------------------------

    if not incident_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident ID cannot be empty.",
        )

    # --------------------------------------------------------
    # Delete through service
    # --------------------------------------------------------

    try:

        deleted = await delete_incident(
            incident_id=incident_id,
            requester_id=user_id,
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete incident.",
        ) from exc

    # --------------------------------------------------------
    # Incident not found
    # --------------------------------------------------------

    if not deleted:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return deleted_response(
        data={
            "incident_id": incident_id,
        },
        message="Incident deleted successfully.",
    )


# ============================================================
# INCIDENT ROUTE INFORMATION
# ============================================================

@router.get(
    "/meta/info",
    status_code=status.HTTP_200_OK,
)
async def incident_api_info() -> dict[str, Any]:
    """
    Development information about incident APIs.

    This endpoint is intentionally simple and does not expose
    incident data.
    """

    return {
        "success": True,
        "status": "success",
        "message": "Incident API information.",
        "data": {
            "endpoints": {
                "create": {
                    "method": "POST",
                    "path": "/incidents",
                    "authentication": True,
                },
                "list": {
                    "method": "GET",
                    "path": "/incidents",
                    "authentication": True,
                },
                "detail": {
                    "method": "GET",
                    "path": "/incidents/{incident_id}",
                    "authentication": True,
                },
                "update": {
                    "method": "PATCH",
                    "path": "/incidents/{incident_id}",
                    "authentication": True,
                },
                "delete": {
                    "method": "DELETE",
                    "path": "/incidents/{incident_id}",
                    "authentication": True,
                },
            }
        },
    }