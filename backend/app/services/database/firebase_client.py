from functools import lru_cache

from firebase_admin import firestore

from app.services.database.firebase_config import (
    initialize_firebase,
)


# ============================================================
# FIRESTORE CLIENT
# ============================================================

@lru_cache(maxsize=1)
def get_firestore_client():

    initialize_firebase()

    return firestore.client()


# ============================================================
# DATABASE OBJECT
# ============================================================

class LazyFirestore:

    def __getattr__(
        self,
        name,
    ):

        db = get_firestore_client()

        return getattr(
            db,
            name,
        )


db = LazyFirestore()