from app.services.database.firebase_client import db


NOTIFICATIONS_COLLECTION = "notifications"


def create_notification(notification_id, data):
    """Create a new notification in Firestore."""

    db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(data)

    return {
        "id": notification_id,
        **data
    }


def get_notification(notification_id):
    """Get a notification from Firestore."""

    doc = db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).get()

    if not doc.exists:
        return None

    return {
        "id": doc.id,
        **doc.to_dict()
    }