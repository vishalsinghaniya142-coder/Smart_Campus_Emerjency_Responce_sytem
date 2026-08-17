from typing import Any, Dict, List, Optional

from app.models.sos import (
    SOS,
    sos_from_document,
    sos_to_document,
)
from app.services.database.firebase_client import db


SOS_COLLECTION = "sos"


class FirebaseSOSRepository:
    """
    Firebase Firestore repository for SOS operations.
    """

    async def create_sos(
        self,
        sos: SOS,
    ) -> SOS:
        data = sos_to_document(sos)

        db.collection(
            SOS_COLLECTION
        ).document(
            sos.id
        ).set(data)

        return sos


    async def get_sos_by_id(
        self,
        sos_id: str,
    ) -> Optional[SOS]:

        document = (
            db.collection(
                SOS_COLLECTION
            )
            .document(
                sos_id
            )
            .get()
        )

        if not document.exists:
            return None

        data = document.to_dict()

        data["id"] = document.id

        return sos_from_document(data)


    async def list_sos_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[SOS]:

        documents = (
            db.collection(
                SOS_COLLECTION
            )
            .where(
                "user_id",
                "==",
                user_id,
            )
            .stream()
        )

        sos_list = []

        for document in documents:
            data = document.to_dict()

            data["id"] = document.id

            try:
                sos = sos_from_document(data)
                sos_list.append(sos)
            except Exception:
                # Ignore old/incompatible SOS documents.
                continue

        return sos_list[
            offset: offset + limit
        ]


    async def update_sos(
        self,
        sos_id: str,
        updates: Dict[str, Any],
    ) -> Optional[SOS]:

        document = (
            db.collection(
                SOS_COLLECTION
            )
            .document(
                sos_id
            )
            .get()
        )

        if not document.exists:
            return None

        db.collection(
            SOS_COLLECTION
        ).document(
            sos_id
        ).update(
            updates
        )

        return await self.get_sos_by_id(
            sos_id
        )