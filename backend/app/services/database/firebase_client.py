from firebase_admin import firestore

from app.services.database.firebase_config import initialize_firebase


# Initialize Firebase Admin SDK
initialize_firebase()

# Firestore database client
db = firestore.client()