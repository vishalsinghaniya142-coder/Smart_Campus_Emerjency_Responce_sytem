from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.models.incident import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.services.database.firebase_client import db


INCIDENTS_COLLECTION = "incidents"


def _serialize_value(value: Any) -> Any:
    """
    Convert Pydantic/Enum values into Firestore-compatible values.
    """

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            key: _serialize_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _serialize_value(item)
            for item in value
        ]

    return value


def _incident_to_firestore_data(
    incident: Incident,
) -> Dict[str, Any]:
    """
    Convert Incident model into Firestore data.
    """

    data = incident.model_dump(
        mode="python",
        exclude_none=True,
    )

    return _serialize_value(data)


def _document_to_incident(
    document,
) -> Optional[Incident]:
    """
    Convert Firestore document into Incident model.
    """

    if not document.exists:
        return None

    data = document.to_dict()

    data["id"] = document.id

    return Incident.model_validate(data)


class FirebaseIncidentRepository:
    """
    Firebase Firestore implementation of IncidentRepository.
    """

    async def create_incident(
        self,
        incident: Incident,
    ) -> Incident:

        data = _incident_to_firestore_data(
            incident
        )

        db.collection(
            INCIDENTS_COLLECTION
        ).document(
            incident.id
        ).set(data)

        return incident


    async def get_incident_by_id(
        self,
        incident_id: str,
    ) -> Optional[Incident]:

        document = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(
                incident_id
            )
            .get()
        )

        return _document_to_incident(
            document
        )


    async def list_incidents(
        self,
        incident_type: Optional[IncidentType] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
        reporter_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Incident]:

        query = db.collection(
            INCIDENTS_COLLECTION
        )

        if incident_type is not None:
            query = query.where(
                "incident_type",
                "==",
                incident_type.value,
            )

        if severity is not None:
            query = query.where(
                "severity",
                "==",
                severity.value,
            )

        if status is not None:
            query = query.where(
                "status",
                "==",
                status.value,
            )

        if reporter_id is not None:
            query = query.where(
                "reporter_id",
                "==",
                reporter_id,
            )

        documents = query.stream()

        incidents = []

        for document in documents:
            incident = _document_to_incident(
                document
            )

            if incident is not None:
                incidents.append(incident)

        return incidents[
            offset: offset + limit
        ]


    async def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Incident]:

        document = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(
                incident_id
            )
            .get()
        )

        if not document.exists:
            return None

        clean_updates = _serialize_value(
            updates
        )

        db.collection(
            INCIDENTS_COLLECTION
        ).document(
            incident_id
        ).update(
            clean_updates
        )

        return await self.get_incident_by_id(
            incident_id
        )


    async def delete_incident(
        self,
        incident_id: str,
    ) -> bool:

        document = (
            db.collection(
                INCIDENTS_COLLECTION
            )
            .document(
                incident_id
            )
            .get()
        )

        if not document.exists:
            return False

        db.collection(
            INCIDENTS_COLLECTION
        ).document(
            incident_id
        ).delete()

        return True