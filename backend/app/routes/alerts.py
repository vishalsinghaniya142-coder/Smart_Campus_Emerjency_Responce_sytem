from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.dependencies import get_current_user

from app.models.alert import (
    AlertAudience,
    AlertSeverity,
    AlertStatus,
    AlertType,
)

from app.schemas.alert_schema import (
    AlertCreateRequest,
    AlertDetailResponse,
    AlertListResponse,
    AlertResponse,
    AlertUpdateRequest,
    build_alert_detail_response,
    build_alert_list_response,
    build_alert_response,
)

from app.services.alert_service import (
    activate_alert,
    cancel_alert,
    create_alert,
    delete_alert,
    get_alert,
    list_active_alerts,
    list_alerts,
    update_alert,
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
# CREATE ALERT
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_alert_route(
    payload: AlertCreateRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Create a new emergency alert.

    Endpoint
    --------
    POST /alerts

    Authentication
    --------------
    Required.

    IMPORTANT:
        created_by is taken from the authenticated user.

    It is never trusted from the request body.
    """

    # --------------------------------------------------------
    # Get authenticated user
    # --------------------------------------------------------

    creator_id = current_user.get(
        "id"
    )

    if not creator_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Create alert through service layer
    # --------------------------------------------------------

    try:

        alert = await create_alert(
            payload=payload,
            creator_id=creator_id,
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
            detail="Unable to create alert.",
        ) from exc

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    response_data = build_alert_response(
        alert
    )

    return created_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alert created successfully.",
    )


# ============================================================
# GET ALERTS
# ============================================================

@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def get_alerts(
    alert_type: Optional[
        AlertType
    ] = Query(
        default=None,
        description="Filter by alert type.",
    ),
    severity: Optional[
        AlertSeverity
    ] = Query(
        default=None,
        description="Filter by alert severity.",
    ),
    audience: Optional[
        AlertAudience
    ] = Query(
        default=None,
        description="Filter by intended audience.",
    ),
    alert_status: Optional[
        AlertStatus
    ] = Query(
        default=None,
        alias="status",
        description="Filter by alert status.",
    ),
    active_only: bool = Query(
        default=False,
        description="Return only active alerts.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of alerts.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of alerts to skip.",
    ),
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Get emergency alerts.

    Endpoint
    --------
    GET /alerts

    Authentication
    --------------
    Required.

    Supported filters:

        alert_type
        severity
        audience
        status
        active_only
        limit
        offset
    """

    # --------------------------------------------------------
    # Authentication
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
    # Fetch alerts
    # --------------------------------------------------------

    try:

        if active_only:

            alerts = await list_active_alerts(
                audience=audience,
                limit=limit,
                offset=offset,
            )

        else:

            alerts = await list_alerts(
                alert_type=alert_type,
                severity=severity,
                audience=audience,
                status=alert_status,
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
            detail="Unable to fetch alerts.",
        ) from exc

    # --------------------------------------------------------
    # Build response
    # --------------------------------------------------------

    response_data = build_alert_list_response(
        alerts
    )

    return resource_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alerts fetched successfully.",
    )


# ============================================================
# GET SINGLE ALERT
# ============================================================

@router.get(
    "/{alert_id}",
    status_code=status.HTTP_200_OK,
)
async def get_alert_by_id(
    alert_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Get one alert by ID.

    Endpoint
    --------
    GET /alerts/{alert_id}

    Authentication
    --------------
    Required.
    """

    # --------------------------------------------------------
    # Authentication
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
    # Validate alert ID
    # --------------------------------------------------------

    if not alert_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert ID cannot be empty.",
        )

    # --------------------------------------------------------
    # Fetch alert
    # --------------------------------------------------------

    try:

        alert = await get_alert(
            alert_id
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
            detail="Unable to fetch alert.",
        ) from exc

    # --------------------------------------------------------
    # Not found
    # --------------------------------------------------------

    if alert is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    response_data = build_alert_detail_response(
        alert
    )

    return resource_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alert fetched successfully.",
    )


# ============================================================
# UPDATE ALERT
# ============================================================

@router.patch(
    "/{alert_id}",
    status_code=status.HTTP_200_OK,
)
async def update_alert_route(
    alert_id: str,
    payload: AlertUpdateRequest,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Update an existing alert.

    Endpoint
    --------
    PATCH /alerts/{alert_id}

    Authentication
    --------------
    Required.

    Ownership verification is performed inside
    alert_service.py.
    """

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    requester_id = current_user.get(
        "id"
    )

    if not requester_id:

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

    if not alert_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert ID cannot be empty.",
        )

    # --------------------------------------------------------
    # Update through service
    # --------------------------------------------------------

    try:

        alert = await update_alert(
            alert_id=alert_id,
            payload=payload,
            requester_id=requester_id,
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
            detail="Unable to update alert.",
        ) from exc

    # --------------------------------------------------------
    # Not found
    # --------------------------------------------------------

    if alert is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    response_data = build_alert_response(
        alert
    )

    return updated_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alert updated successfully.",
    )


# ============================================================
# ACTIVATE ALERT
# ============================================================

@router.post(
    "/{alert_id}/activate",
    status_code=status.HTTP_200_OK,
)
async def activate_alert_route(
    alert_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Activate an existing alert.

    Endpoint
    --------
    POST /alerts/{alert_id}/activate
    """

    requester_id = current_user.get(
        "id"
    )

    if not requester_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:

        alert = await activate_alert(
            alert_id=alert_id,
            requester_id=requester_id,
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
            detail="Unable to activate alert.",
        ) from exc

    if alert is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    response_data = build_alert_response(
        alert
    )

    return updated_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alert activated successfully.",
    )


# ============================================================
# CANCEL ALERT
# ============================================================

@router.post(
    "/{alert_id}/cancel",
    status_code=status.HTTP_200_OK,
)
async def cancel_alert_route(
    alert_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Cancel an active alert.

    Endpoint
    --------
    POST /alerts/{alert_id}/cancel
    """

    requester_id = current_user.get(
        "id"
    )

    if not requester_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:

        alert = await cancel_alert(
            alert_id=alert_id,
            requester_id=requester_id,
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
            detail="Unable to cancel alert.",
        ) from exc

    if alert is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    response_data = build_alert_response(
        alert
    )

    return updated_response(
        data=response_data.model_dump(
            mode="json"
        ),
        message="Alert cancelled successfully.",
    )


# ============================================================
# DELETE ALERT
# ============================================================

@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_alert_route(
    alert_id: str,
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> dict[str, Any]:
    """
    Delete an alert.

    Endpoint
    --------
    DELETE /alerts/{alert_id}

    Active alerts cannot normally be deleted. They should be
    cancelled instead.
    """

    requester_id = current_user.get(
        "id"
    )

    if not requester_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user could not be identified.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not alert_id.strip():

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert ID cannot be empty.",
        )

    try:

        deleted = await delete_alert(
            alert_id=alert_id,
            requester_id=requester_id,
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
            detail="Unable to delete alert.",
        ) from exc

    if not deleted:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    return deleted_response(
        data={
            "alert_id": alert_id,
        },
        message="Alert deleted successfully.",
    )


# ============================================================
# ALERT API INFORMATION
# ============================================================

@router.get(
    "/meta/info",
    status_code=status.HTTP_200_OK,
)
async def alert_api_info() -> dict[str, Any]:
    """
    Development information about alert endpoints.

    This endpoint does not expose private alert data.
    """

    return {
        "success": True,
        "status": "success",
        "message": "Alert API information.",
        "data": {
            "endpoints": {
                "create": {
                    "method": "POST",
                    "path": "/alerts",
                    "authentication": True,
                },
                "list": {
                    "method": "GET",
                    "path": "/alerts",
                    "authentication": True,
                },
                "detail": {
                    "method": "GET",
                    "path": "/alerts/{alert_id}",
                    "authentication": True,
                },
                "update": {
                    "method": "PATCH",
                    "path": "/alerts/{alert_id}",
                    "authentication": True,
                },
                "activate": {
                    "method": "POST",
                    "path": "/alerts/{alert_id}/activate",
                    "authentication": True,
                },
                "cancel": {
                    "method": "POST",
                    "path": "/alerts/{alert_id}/cancel",
                    "authentication": True,
                },
                "delete": {
                    "method": "DELETE",
                    "path": "/alerts/{alert_id}",
                    "authentication": True,
                },
            }
        },
    }