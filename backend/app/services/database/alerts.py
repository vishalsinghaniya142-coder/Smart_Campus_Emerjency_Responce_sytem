from enum import Enum
from typing import Any, Dict, List, Optional

from app.models.alert import (
    Alert,
    AlertAudience,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.services.database.firebase_client import db


ALERTS_COLLECTION = "alerts"


def _serialize_value(value: Any) -> Any:
    """Convert model values into Firestore-compatible values."""

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


def _alert_to_firestore_data(
    alert: Alert,
) -> Dict[str, Any]:
    """Convert Alert model to Firestore data."""

    data = alert.model_dump(
        mode="python",
        exclude_none=True,
    )

    return _serialize_value(data)


def _document_to_alert(
    document,
) -> Optional[Alert]:
    """Convert Firestore document to Alert model."""

    if not document.exists:
        return None

    data = document.to_dict()

    data["id"] = document.id

    try:
        return Alert.model_validate(data)
    except Exception:
        # Ignore old/incompatible Firestore documents.
        # Existing Firebase data is NOT modified or deleted.
        return None


class FirebaseAlertRepository:
    """Firebase Firestore implementation of AlertRepository."""

    async def create_alert(
        self,
        alert: Alert,
    ) -> Alert:

        data = _alert_to_firestore_data(
            alert
        )

        db.collection(
            ALERTS_COLLECTION
        ).document(
            alert.id
        ).set(data)

        return alert


    async def get_alert_by_id(
        self,
        alert_id: str,
    ) -> Optional[Alert]:

        document = (
            db.collection(
                ALERTS_COLLECTION
            )
            .document(
                alert_id
            )
            .get()
        )

        return _document_to_alert(
            document
        )


    async def list_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        audience: Optional[AlertAudience] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Alert]:

        query = db.collection(
            ALERTS_COLLECTION
        )

        if alert_type is not None:
            query = query.where(
                "alert_type",
                "==",
                alert_type.value,
            )

        if severity is not None:
            query = query.where(
                "severity",
                "==",
                severity.value,
            )

        if audience is not None:
            query = query.where(
                "audience",
                "==",
                audience.value,
            )

        if status is not None:
            query = query.where(
                "status",
                "==",
                status.value,
            )

        documents = query.stream()

        alerts = []

        for document in documents:
            alert = _document_to_alert(
                document
            )

            if alert is not None:
                alerts.append(alert)

        return alerts[
            offset: offset + limit
        ]


    async def update_alert(
        self,
        alert_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Alert]:

        document = (
            db.collection(
                ALERTS_COLLECTION
            )
            .document(
                alert_id
            )
            .get()
        )

        if not document.exists:
            return None

        clean_updates = _serialize_value(
            updates
        )

        db.collection(
            ALERTS_COLLECTION
        ).document(
            alert_id
        ).update(
            clean_updates
        )

        return await self.get_alert_by_id(
            alert_id
        )


    async def delete_alert(
        self,
        alert_id: str,
    ) -> bool:

        document = (
            db.collection(
                ALERTS_COLLECTION
            )
            .document(
                alert_id
            )
            .get()
        )

        if not document.exists:
            return False

        db.collection(
            ALERTS_COLLECTION
        ).document(
            alert_id
        ).delete()

        return True