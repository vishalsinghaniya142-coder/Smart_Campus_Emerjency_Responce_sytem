from app.services.database.firebase_client import db


ALERTS_COLLECTION = "alerts"


def create_alert(alert_id, data):
    """Create a new emergency alert in Firestore."""

    db.collection(ALERTS_COLLECTION).document(alert_id).set(data)

    return {
        "id": alert_id,
        **data
    }


def get_alert(alert_id):
    """Get an alert from Firestore."""

    doc = db.collection(ALERTS_COLLECTION).document(alert_id).get()

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict()
    }