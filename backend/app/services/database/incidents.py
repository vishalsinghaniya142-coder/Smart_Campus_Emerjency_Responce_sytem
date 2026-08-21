from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.database.firebase_client import db
from app.models.incident import (
    Incident,
    IncidentType,
    IncidentSeverity,
    IncidentStatus,
)


INCIDENTS_COLLECTION = "incidents"


def _normalize_firestore_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {
            key: _normalize_firestore_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_firestore_value(item) for item in value]
    return value


def _normalize_legacy_incident(data: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    data.setdefault("reporter_id", data.get("user_id", "system"))
    data.setdefault("incident_type", data.get("type", "other"))
    data.setdefault("title", data.get("name", "Emergency Incident"))
    data.setdefault(
        "description",
        data.get("message", data.get("details", "Please review this incident.")),
    )
    data.setdefault("severity", data.get("severity"))
    data.setdefault("images", [])
    data.setdefault("ai_analysis", None)
    data.setdefault("resolved_at", None)
    data.setdefault("created_at", now)
    data.setdefault("updated_at", data["created_at"])
    if isinstance(data.get("location"), str):
        data["location"] = {
            "latitude": 0,
            "longitude": 0,
            "address": data["location"],
        }
    data.setdefault("location", {"latitude": 0, "longitude": 0})
    if data.get("status") == "active":
        data["status"] = "reported"
    return data


class FirebaseIncidentRepository:
    """Firebase/Firestore implementation of IncidentRepository."""

    async def create_incident(
        self,
        incident: Incident,
    ) -> Incident:
        data = _normalize_firestore_value(
            incident.model_dump(mode="python")
        )

        incident_id = incident.id

        db.collection(
            INCIDENTS_COLLECTION
        ).document(incident_id).set(data)

        return incident

    async def get_incident_by_id(
        self,
        incident_id: str,
    ) -> Optional[Incident]:

        doc = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(incident_id)
            .get()
        )

        if not doc.exists:
            return None

        data = _normalize_legacy_incident(doc.to_dict() or {})

        data["id"] = doc.id

        return Incident.model_validate(data)

    async def list_incidents(
        self,
        incident_type: Optional[IncidentType] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
        reporter_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Incident]:

        documents = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .stream()
        )

        incidents = []

        for doc in documents:

            data = _normalize_legacy_incident(doc.to_dict() or {})
            data["id"] = doc.id

            incident = Incident.model_validate(data)

            if (
                incident_type is not None
                and incident.incident_type != incident_type
            ):
                continue

            if (
                severity is not None
                and incident.severity != severity
            ):
                continue

            if (
                status is not None
                and incident.status != status
            ):
                continue

            if (
                reporter_id is not None
                and incident.reporter_id != reporter_id
            ):
                continue

            incidents.append(incident)

        incidents.sort(
            key=lambda x: x.created_at,
            reverse=True,
        )

        return incidents[
            offset:offset + limit
        ]

    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Incident]:

        doc_ref = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(incident_id)
        )

        doc = doc_ref.get()

        if not doc.exists:
            return None

        clean_updates = {}

        for key, value in updates.items():

            if hasattr(value, "value"):
                value = value.value

            if isinstance(value, Enum):
                value = value.value

            clean_updates[key] = value

        doc_ref.update(clean_updates)

        return await self.get_incident_by_id(
            incident_id
        )

    async def delete_incident(
        self,
        incident_id: str,
    ) -> bool:

        doc_ref = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(incident_id)
        )

        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()

        return True


# ------------------------------------------------------------
# Backward-compatible helper functions
# ------------------------------------------------------------

def create_incident(
    incident_id,
    data,
):
    """Create a new emergency incident."""

    db.collection(
        INCIDENTS_COLLECTION
    ).document(incident_id).set(data)

    return {
        "id": incident_id,
        **data,
    }


def get_incident(
    incident_id,
):
    """Get an incident from Firestore."""

    doc = (
        db.collection(
            INCIDENTS_COLLECTION
        )
        .document(incident_id)
        .get()
    )

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict(),
    }