import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.models.incident import (
    Incident,
    IncidentAIAnalysis,
    IncidentCreate,
    IncidentLocation,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    IncidentUpdate,
    build_incident,
    incident_to_public,
)
from app.schemas.incident_schema import (
    IncidentCreateRequest,
    IncidentUpdateRequest,
    create_request_to_model_data,
    update_request_to_model_data,
)


# ============================================================
# DATABASE REPOSITORY CONTRACT
# ============================================================
#
# IMPORTANT:
#
# This service does NOT directly import Firebase.
#
# The actual database implementation will be provided through
# a repository/integration layer.
#
# Architecture:
#
# incident_service.py
#        |
#        v
# IncidentRepository
#        |
#        v
# Member 4 database service
#        |
#        v
# Firebase
#
# This keeps the backend independent from the concrete
# database implementation.
# ============================================================


class IncidentRepository(Protocol):
    """
    Contract required from the incident database layer.
    """

    async def create_incident(
        self,
        incident: Incident,
    ) -> Incident:
        """
        Persist a new incident.
        """
        ...

    async def get_incident_by_id(
        self,
        incident_id: str,
    ) -> Optional[Incident]:
        """
        Retrieve an incident by ID.
        """
        ...

    async def list_incidents(
        self,
        incident_type: Optional[IncidentType] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
        reporter_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Incident]:
        """
        Retrieve incidents using optional filters.
        """
        ...

    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Incident]:
        """
        Update an existing incident.
        """
        ...

    async def delete_incident(
        self,
        incident_id: str,
    ) -> bool:
        """
        Delete an incident.
        """
        ...


# ============================================================
# AI SERVICE CONTRACT
# ============================================================
#
# Member 3's AI implementation can be connected here.
#
# The service should be able to analyze incident information
# and return an IncidentAIAnalysis object.
#
# Actual Gemini / ML / vision code stays outside this file.
# ============================================================


class IncidentAIService(Protocol):
    """
    Contract for incident AI analysis.
    """

    async def analyze_incident(
        self,
        incident: Incident,
    ) -> Optional[IncidentAIAnalysis]:
        """
        Analyze an incident and return AI results.
        """
        ...


# ============================================================
# REPOSITORY / AI INSTANCES
# ============================================================

_incident_repository: Optional[
    IncidentRepository
] = None

_incident_ai_service: Optional[
    IncidentAIService
] = None

_incident_notification_service: Optional[Any] = None

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURE DATABASE REPOSITORY
# ============================================================


def configure_incident_repository(
    repository: IncidentRepository,
) -> None:
    """
    Register the concrete incident repository.

    The repository can later be implemented using Firebase.
    """

    global _incident_repository

    if repository is None:
        raise ValueError(
            "Incident repository cannot be None."
        )

    _incident_repository = repository


# ============================================================
# GET DATABASE REPOSITORY
# ============================================================


def get_incident_repository() -> IncidentRepository:
    """
    Return the configured incident repository.
    """

    if _incident_repository is None:

        raise RuntimeError(
            "Incident repository is not configured."
        )

    return _incident_repository


# ============================================================
# CONFIGURE AI SERVICE
# ============================================================


def configure_incident_ai_service(
    ai_service: IncidentAIService,
) -> None:
    """
    Register the concrete AI service.

    Member 3's implementation can be connected here.
    """

    global _incident_ai_service

    if ai_service is None:
        raise ValueError(
            "Incident AI service cannot be None."
        )

    _incident_ai_service = ai_service


# ============================================================
# GET AI SERVICE
# ============================================================


def get_incident_ai_service() -> Optional[
    IncidentAIService
]:
    """
    Return the configured AI service.

    None is allowed because an incident can still be created
    even when AI analysis is temporarily unavailable.
    """

    return _incident_ai_service


def configure_incident_notification_service(
    notification_service: Any,
) -> None:
    """Register the concrete incident notification service."""
    global _incident_notification_service
    if notification_service is None:
        raise ValueError("Incident notification service cannot be None.")
    _incident_notification_service = notification_service


def get_incident_notification_service() -> Optional[Any]:
    """Return the configured incident notification service."""
    return _incident_notification_service


# ============================================================
# CREATE INCIDENT
# ============================================================


async def create_incident(
    payload: IncidentCreateRequest,
    reporter_id: str,
) -> Incident:
    """
    Create a new emergency incident.

    Flow:

        API Request
             |
             v
        Validate schema
             |
             v
        authenticated reporter_id
             |
             v
        Build Incident
             |
             +----------------+
             |                |
             v                v
        AI analysis       Database
             |                |
             +-------+--------+
                     |
                     v
              Stored Incident
    """

    # --------------------------------------------------------
    # Validate reporter identity
    # --------------------------------------------------------

    if not reporter_id:

        raise ValueError(
            "Authenticated reporter ID is required."
        )

    # --------------------------------------------------------
    # Convert API schema to model data
    # --------------------------------------------------------

    data = create_request_to_model_data(
        payload=payload,
        reporter_id=reporter_id,
    )

    # --------------------------------------------------------
    # Build IncidentCreate object
    # --------------------------------------------------------

    incident_data = IncidentCreate(
        reporter_id=data["reporter_id"],
        incident_type=data["incident_type"],
        title=data["title"],
        description=data["description"],
        location=data["location"],
        severity=data.get("severity"),
        status=IncidentStatus.REPORTED,
        images=data.get("images", []),
    )

    # --------------------------------------------------------
    # Generate incident ID
    # --------------------------------------------------------

    incident_id = generate_incident_id(
        reporter_id=reporter_id
    )

    # --------------------------------------------------------
    # Build complete Incident model
    # --------------------------------------------------------

    incident = build_incident(
        incident_id=incident_id,
        reporter_id=incident_data.reporter_id,
        incident_type=incident_data.incident_type,
        title=incident_data.title,
        description=incident_data.description,
        location=incident_data.location,
        severity=incident_data.severity,
        status=incident_data.status,
        images=incident_data.images,
    )

    # --------------------------------------------------------
    # Optional AI analysis
    # --------------------------------------------------------
    #
    # AI is intentionally optional.
    #
    # If Member 3's AI service is connected:
    #
    #     incident -> AI -> analysis
    #
    # If AI is unavailable:
    #
    #     incident creation should not necessarily fail.
    # --------------------------------------------------------

    ai_service = get_incident_ai_service()

    if ai_service is not None:

        try:

            analysis = (
                await ai_service.analyze_incident(
                    incident
                )
            )

            if analysis is not None:

                incident.ai_analysis = analysis

                # If AI provides a severity and the user did not
                # explicitly provide one, use the AI result.
                if (
                    incident.severity is None
                    and analysis.severity is not None
                ):

                    incident.severity = (
                        analysis.severity
                    )

        except Exception:
            # ------------------------------------------------
            # AI failure should not destroy the emergency
            # incident itself.
            #
            # Production logging can be added later.
            # ------------------------------------------------
            pass

    # --------------------------------------------------------
    # Persist incident
    # --------------------------------------------------------

    repository = get_incident_repository()

    stored_incident = (
        await repository.create_incident(
            incident
        )
    )

    notification_service = get_incident_notification_service()
    if notification_service is not None:
        try:
            await notification_service.send_incident_notification(stored_incident)
        except Exception as exc:
            logger.warning(f"Incident SMS broadcast failed after save: {exc}")

    return stored_incident


# ============================================================
# GET INCIDENT
# ============================================================


async def get_incident(
    incident_id: str,
) -> Optional[Incident]:
    """
    Retrieve one incident by ID.
    """

    if not incident_id:

        raise ValueError(
            "Incident ID is required."
        )

    repository = get_incident_repository()

    return await repository.get_incident_by_id(
        incident_id
    )


# ============================================================
# GET INCIDENT FOR REPORTER
# ============================================================


async def get_reporter_incident(
    incident_id: str,
    reporter_id: str,
) -> Optional[Incident]:
    """
    Retrieve an incident while ensuring it belongs to the
    authenticated reporter.

    This prevents a user from reading another user's private
    incident through an ID alone.
    """

    if not incident_id:

        raise ValueError(
            "Incident ID is required."
        )

    if not reporter_id:

        raise ValueError(
            "Reporter ID is required."
        )

    incident = await get_incident(
        incident_id
    )

    if incident is None:
        return None

    if incident.reporter_id != reporter_id:

        raise PermissionError(
            "You do not have permission to access this incident."
        )

    return incident


# ============================================================
# LIST INCIDENTS
# ============================================================


async def list_incidents(
    incident_type: Optional[IncidentType] = None,
    severity: Optional[IncidentSeverity] = None,
    status: Optional[IncidentStatus] = None,
    reporter_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Incident]:
    """
    Retrieve incidents with optional filters.

    Supported filters:

        incident_type
        severity
        status
        reporter_id
        limit
        offset
    """

    # --------------------------------------------------------
    # Pagination validation
    # --------------------------------------------------------

    if limit < 1:
        raise ValueError(
            "Limit must be at least 1."
        )

    if limit > 100:
        raise ValueError(
            "Limit cannot exceed 100."
        )

    if offset < 0:
        raise ValueError(
            "Offset cannot be negative."
        )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    repository = get_incident_repository()

    incidents = await repository.list_incidents(
        incident_type=incident_type,
        severity=severity,
        status=status,
        reporter_id=reporter_id,
        limit=limit,
        offset=offset,
    )

    return incidents


# ============================================================
# LIST ACTIVE INCIDENTS
# ============================================================


async def list_active_incidents(
    limit: int = 20,
    offset: int = 0,
) -> List[Incident]:
    """
    Return currently active incidents.

    Active statuses:

        reported
        acknowledged
        in_progress
    """

    repository = get_incident_repository()

    results: List[Incident] = []

    for active_status in (
        IncidentStatus.REPORTED,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.IN_PROGRESS,
    ):

        incidents = await repository.list_incidents(
            status=active_status,
            limit=limit,
            offset=offset,
        )

        results.extend(
            incidents
        )

    # --------------------------------------------------------
    # Sort newest first.
    # --------------------------------------------------------

    results.sort(
        key=lambda incident: incident.created_at,
        reverse=True,
    )

    return results[:limit]


# ============================================================
# UPDATE INCIDENT
# ============================================================


async def update_incident(
    incident_id: str,
    payload: IncidentUpdateRequest,
    requester_id: str,
) -> Optional[Incident]:
    """
    Update an incident.

    Only the incident reporter is allowed to update it through
    this normal user-level service.

    Administrative update logic can be added separately later.
    """

    if not incident_id:

        raise ValueError(
            "Incident ID is required."
        )

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    # --------------------------------------------------------
    # Get existing incident
    # --------------------------------------------------------

    incident = await get_incident(
        incident_id
    )

    if incident is None:
        return None

    # --------------------------------------------------------
    # Ownership check
    # --------------------------------------------------------

    if incident.reporter_id != requester_id:

        raise PermissionError(
            "You do not have permission to update this incident."
        )

    # --------------------------------------------------------
    # Prevent updates after resolution/cancellation.
    # --------------------------------------------------------

    if incident.status in {
        IncidentStatus.RESOLVED,
        IncidentStatus.CANCELLED,
    }:

        raise ValueError(
            "Resolved or cancelled incidents cannot be updated."
        )

    # --------------------------------------------------------
    # Convert request to update data
    # --------------------------------------------------------

    updates = update_request_to_model_data(
        payload
    )

    if not updates:

        raise ValueError(
            "No incident fields were provided for update."
        )

    # --------------------------------------------------------
    # Prevent reporter/status manipulation through a normal
    # profile-like update if necessary.
    #
    # Status is allowed here because the service still validates
    # lifecycle transitions below.
    # --------------------------------------------------------

    if "status" in updates:

        validate_status_transition(
            current_status=incident.status,
            new_status=updates["status"],
        )

    # --------------------------------------------------------
    # Update timestamp
    # --------------------------------------------------------

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    # --------------------------------------------------------
    # Resolution timestamp
    # --------------------------------------------------------

    if (
        updates.get("status")
        == IncidentStatus.RESOLVED
    ):

        updates["resolved_at"] = (
            datetime.now(
                timezone.utc
            )
        )

    # --------------------------------------------------------
    # Database update
    # --------------------------------------------------------

    repository = get_incident_repository()

    updated_incident = (
        await repository.update_incident(
            incident_id,
            updates,
        )
    )

    return updated_incident


# ============================================================
# UPDATE INCIDENT STATUS
# ============================================================


async def update_incident_status(
    incident_id: str,
    new_status: IncidentStatus,
    requester_id: str,
) -> Optional[Incident]:
    """
    Update only an incident's status.

    Useful for dedicated workflow operations.
    """

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    incident = await get_incident(
        incident_id
    )

    if incident is None:
        return None

    if incident.reporter_id != requester_id:

        raise PermissionError(
            "You do not have permission to update this incident."
        )

    validate_status_transition(
        current_status=incident.status,
        new_status=new_status,
    )

    now = datetime.now(
        timezone.utc
    )

    updates: Dict[str, Any] = {
        "status": new_status,
        "updated_at": now,
    }

    if new_status == IncidentStatus.RESOLVED:

        updates["resolved_at"] = now

    elif new_status != IncidentStatus.RESOLVED:

        updates["resolved_at"] = None

    repository = get_incident_repository()

    return await repository.update_incident(
        incident_id,
        updates,
    )


# ============================================================
# RESOLVE INCIDENT
# ============================================================


async def resolve_incident(
    incident_id: str,
    requester_id: str,
) -> Optional[Incident]:
    """
    Mark an incident as resolved.
    """

    return await update_incident_status(
        incident_id=incident_id,
        new_status=IncidentStatus.RESOLVED,
        requester_id=requester_id,
    )


# ============================================================
# CANCEL INCIDENT
# ============================================================


async def cancel_incident(
    incident_id: str,
    requester_id: str,
) -> Optional[Incident]:
    """
    Mark an incident as cancelled.
    """

    return await update_incident_status(
        incident_id=incident_id,
        new_status=IncidentStatus.CANCELLED,
        requester_id=requester_id,
    )


# ============================================================
# DELETE INCIDENT
# ============================================================


async def delete_incident(
    incident_id: str,
    requester_id: str,
) -> bool:
    """
    Delete an incident after ownership verification.
    """

    if not incident_id:

        raise ValueError(
            "Incident ID is required."
        )

    if not requester_id:

        raise ValueError(
            "Authenticated requester ID is required."
        )

    incident = await get_incident(
        incident_id
    )

    if incident is None:
        return False

    if incident.reporter_id != requester_id:

        raise PermissionError(
            "You do not have permission to delete this incident."
        )

    # --------------------------------------------------------
    # Do not allow deleting active emergency records.
    #
    # This is a deliberate safety/data-integrity rule.
    # --------------------------------------------------------

    if incident.status in {
        IncidentStatus.REPORTED,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.IN_PROGRESS,
    }:

        raise ValueError(
            "Active incidents cannot be deleted."
        )

    repository = get_incident_repository()

    return await repository.delete_incident(
        incident_id
    )


# ============================================================
# AI ANALYSIS
# ============================================================


async def analyze_incident(
    incident_id: str,
) -> Optional[IncidentAIAnalysis]:
    """
    Run AI analysis for an existing incident.

    Actual AI implementation belongs to Member 3.

    This function only coordinates:

        incident
            |
            v
        AI service
            |
            v
        analysis
            |
            v
        database update
    """

    incident = await get_incident(
        incident_id
    )

    if incident is None:

        raise ValueError(
            "Incident not found."
        )

    ai_service = get_incident_ai_service()

    if ai_service is None:

        raise RuntimeError(
            "Incident AI service is not configured."
        )

    analysis = await ai_service.analyze_incident(
        incident
    )

    if analysis is None:

        return None

    # --------------------------------------------------------
    # Store analysis result
    # --------------------------------------------------------

    updates: Dict[str, Any] = {
        "ai_analysis": analysis,
        "updated_at": datetime.now(
            timezone.utc
        ),
    }

    # --------------------------------------------------------
    # AI severity can fill missing severity.
    #
    # Existing explicit severity is not automatically
    # overwritten.
    # --------------------------------------------------------

    if (
        incident.severity is None
        and analysis.severity is not None
    ):

        updates["severity"] = (
            analysis.severity
        )

    repository = get_incident_repository()

    await repository.update_incident(
        incident_id,
        updates,
    )

    return analysis


# ============================================================
# STATUS TRANSITION VALIDATION
# ============================================================


def validate_status_transition(
    current_status: IncidentStatus,
    new_status: IncidentStatus,
) -> None:
    """
    Validate basic incident lifecycle transitions.

    Allowed examples:

        reported
            -> acknowledged
            -> in_progress
            -> resolved

        reported
            -> cancelled

    Invalid transitions are rejected.
    """

    if current_status == new_status:
        return

    allowed_transitions = {
        IncidentStatus.REPORTED: {
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.IN_PROGRESS,
            IncidentStatus.CANCELLED,
        },

        IncidentStatus.ACKNOWLEDGED: {
            IncidentStatus.IN_PROGRESS,
            IncidentStatus.CANCELLED,
        },

        IncidentStatus.IN_PROGRESS: {
            IncidentStatus.RESOLVED,
            IncidentStatus.CANCELLED,
        },

        IncidentStatus.RESOLVED: set(),

        IncidentStatus.CANCELLED: set(),
    }

    allowed = allowed_transitions.get(
        current_status,
        set(),
    )

    if new_status not in allowed:

        raise ValueError(
            f"Invalid incident status transition: "
            f"{current_status.value} -> {new_status.value}"
        )


# ============================================================
# INCIDENT ID GENERATOR
# ============================================================


def generate_incident_id(
    reporter_id: str,
) -> str:
    """
    Generate an application-level incident ID.

    The concrete Firebase repository may replace this ID with
    its own document ID if required.

    This identifier is not a security credential.
    """

    import hashlib
    import uuid

    if not reporter_id:

        raise ValueError(
            "Reporter ID is required."
        )

    timestamp = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    raw_value = (
        f"{reporter_id}:"
        f"{timestamp}:"
        f"{uuid.uuid4()}"
    )

    digest = hashlib.sha256(
        raw_value.encode(
            "utf-8"
        )
    ).hexdigest()

    return f"inc_{digest[:24]}"


# ============================================================
# INCIDENT PUBLIC DATA
# ============================================================


def to_public_incident(
    incident: Incident,
) -> dict:
    """
    Convert an Incident object into safe API data.
    """

    public_incident = incident_to_public(
        incident
    )

    return public_incident.model_dump(
        mode="json"
    )


# ============================================================
# INCIDENT OWNERSHIP CHECK
# ============================================================


def user_owns_incident(
    incident: Incident,
    user_id: str,
) -> bool:
    """
    Check whether a user owns an incident.
    """

    if not user_id:
        return False

    return (
        incident.reporter_id
        == user_id
    )


# ============================================================
# INCIDENT SEVERITY CHECK
# ============================================================


def is_high_priority_incident(
    incident: Incident,
) -> bool:
    """
    Determine whether an incident requires high-priority
    handling.

    Critical and high incidents are considered high priority.
    """

    return incident.severity in {
        IncidentSeverity.HIGH,
        IncidentSeverity.CRITICAL,
    }


# ============================================================
# INCIDENT ACTIVE CHECK
# ============================================================


def is_active_incident(
    incident: Incident,
) -> bool:
    """
    Determine whether the incident is still active.
    """

    return incident.status in {
        IncidentStatus.REPORTED,
        IncidentStatus.ACKNOWLEDGED,
        IncidentStatus.IN_PROGRESS,
    }