from datetime import datetime, timezone
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


class FirebaseAlertRepository:
    """Firestore implementation of the alert service repository."""

    def __init__(self) -> None:
        self.collection = db.collection(ALERTS_COLLECTION)

    @staticmethod
    def _document_to_alert(document: Any) -> Alert:
        data = document.to_dict() or {}
        data["id"] = document.id

        # Keep older alert documents readable after the schema grew.
        data.setdefault("created_by", data.get("user_id", "system"))
        data.setdefault("title", data.get("name", "Emergency Alert"))
        data.setdefault(
            "message",
            data.get("description", data.get("details", "Please stay alert.")),
        )
        data.setdefault("alert_type", data.get("type", AlertType.EMERGENCY.value))
        data.setdefault("severity", AlertSeverity.MEDIUM.value)
        data.setdefault("audience", AlertAudience.ALL.value)
        data.setdefault("status", AlertStatus.ACTIVE.value)
        data.setdefault("created_at", datetime.now(timezone.utc))
        data.setdefault("updated_at", data["created_at"])
        return Alert.model_validate(data)

    @staticmethod
    def _alert_data(alert: Alert) -> Dict[str, Any]:
        return FirebaseAlertRepository._normalize_firestore_value(
            alert.model_dump(mode="python")
        )

    @staticmethod
    def _normalize_firestore_value(value: Any) -> Any:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {
                key: FirebaseAlertRepository._normalize_firestore_value(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                FirebaseAlertRepository._normalize_firestore_value(item)
                for item in value
            ]
        return value

    async def create_alert(self, alert: Alert) -> Alert:
        self.collection.document(alert.id).set(
            self._alert_data(alert)
        )
        return alert

    async def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        document = self.collection.document(alert_id).get()
        if not document.exists:
            return None
        return self._document_to_alert(document)

    async def list_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        audience: Optional[AlertAudience] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Alert]:
        alerts = [
            self._document_to_alert(document)
            for document in self.collection.stream()
        ]

        if alert_type is not None:
            alerts = [item for item in alerts if item.alert_type == alert_type]
        if severity is not None:
            alerts = [item for item in alerts if item.severity == severity]
        if audience is not None:
            alerts = [item for item in alerts if item.audience == audience]
        if status is not None:
            alerts = [item for item in alerts if item.status == status]

        alerts.sort(
            key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return alerts[offset:offset + limit]

    async def update_alert(
        self,
        alert_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Alert]:
        document_ref = self.collection.document(alert_id)
        document = document_ref.get()
        if not document.exists:
            return None

        update_data = dict(updates)
        update_data = self._normalize_firestore_value(update_data)

        document_ref.update(update_data)
        updated_document = document_ref.get()
        return self._document_to_alert(updated_document)

    async def delete_alert(self, alert_id: str) -> bool:
        document_ref = self.collection.document(alert_id)
        if not document_ref.get().exists:
            return False
        document_ref.delete()
        return True