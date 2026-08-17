from typing import List, Optional

from app.models.shelter import (
    Shelter,
    ShelterCreate,
    ShelterListItem,
    ShelterPublic,
    ShelterSearchResult,
    ShelterUpdate,
    build_shelter,
    get_available_capacity,
    shelter_from_document,
    shelter_to_document,
    shelter_to_list_item,
    shelter_to_public,
    build_shelter_search_result,
)

from app.services.database.firebase_client import db


SHELTERS_COLLECTION = "shelters"


# ============================================================
# CREATE SHELTER
# ============================================================

async def create_shelter(
    payload: ShelterCreate,
) -> Shelter:

    document_ref = db.collection(
        SHELTERS_COLLECTION
    ).document()

    shelter = build_shelter(
        shelter_id=document_ref.id,
        name=payload.name,
        location=payload.location,
        shelter_type=payload.shelter_type,
        description=payload.description,
        capacity=payload.capacity,
        amenities=payload.amenities,
        status=payload.status,
        contact_number=payload.contact_number,
        created_by=payload.created_by,
    )

    document_ref.set(
        shelter_to_document(shelter)
    )

    return shelter


# ============================================================
# GET SHELTER BY ID
# ============================================================

async def get_shelter_by_id(
    shelter_id: str,
) -> Optional[Shelter]:

    document = (
        db.collection(
            SHELTERS_COLLECTION
        )
        .document(shelter_id)
        .get()
    )

    if not document.exists:
        return None

    data = document.to_dict()

    if data is None:
        return None

    data["id"] = document.id

    return shelter_from_document(data)


# ============================================================
# LIST SHELTERS
# ============================================================

async def list_shelters(
    limit: int = 20,
    offset: int = 0,
) -> List[Shelter]:

    documents = (
        db.collection(
            SHELTERS_COLLECTION
        )
        .stream()
    )

    shelters = []

    for index, document in enumerate(documents):

        if index < offset:
            continue

        if len(shelters) >= limit:
            break

        data = document.to_dict()

        if data is None:
            continue

        data["id"] = document.id

        try:
            shelters.append(
                shelter_from_document(data)
            )
        except Exception:
            # Ignore malformed database documents.
            continue

    return shelters


# ============================================================
# UPDATE SHELTER
# ============================================================

async def update_shelter(
    shelter_id: str,
    payload: ShelterUpdate,
) -> Optional[Shelter]:

    document_ref = (
        db.collection(
            SHELTERS_COLLECTION
        )
        .document(shelter_id)
    )

    document = document_ref.get()

    if not document.exists:
        return None

    current = document.to_dict()

    if current is None:
        return None

    current["id"] = document.id

    shelter = shelter_from_document(
        current
    )

    updates = payload.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not updates:
        return shelter

    update_data = {}

    for field, value in updates.items():

        if hasattr(value, "model_dump"):
            value = value.model_dump(
                mode="json"
            )

        elif hasattr(value, "value"):
            value = value.value

        update_data[field] = value

    from datetime import datetime, timezone

    update_data["updated_at"] = datetime.now(
        timezone.utc
    )

    document_ref.update(
        update_data
    )

    return await get_shelter_by_id(
        shelter_id
    )


# ============================================================
# DELETE SHELTER
# ============================================================

async def delete_shelter(
    shelter_id: str,
) -> bool:

    document_ref = (
        db.collection(
            SHELTERS_COLLECTION
        )
        .document(shelter_id)
    )

    document = document_ref.get()

    if not document.exists:
        return False

    document_ref.delete()

    return True


# ============================================================
# PUBLIC SHELTER LIST
# ============================================================

async def list_public_shelters(
    limit: int = 20,
    offset: int = 0,
) -> List[ShelterListItem]:

    shelters = await list_shelters(
        limit=limit,
        offset=offset,
    )

    return [
        shelter_to_list_item(shelter)
        for shelter in shelters
    ]


# ============================================================
# PUBLIC SHELTER
# ============================================================

async def get_public_shelter(
    shelter_id: str,
) -> Optional[ShelterPublic]:

    shelter = await get_shelter_by_id(
        shelter_id
    )

    if shelter is None:
        return None

    return shelter_to_public(
        shelter
    )


# ============================================================
# NEAREST SHELTER
# ============================================================

async def find_nearest_shelters(
    latitude: float,
    longitude: float,
    limit: int = 5,
) -> List[ShelterSearchResult]:

    shelters = await list_shelters(
        limit=100,
        offset=0,
    )

    results = []

    # Temporary straight-line distance calculation.
    #
    # Later this can be replaced/combined with the
    # Member 4 Maps / routing layer.

    from math import radians, sin, cos, sqrt, atan2

    earth_radius = 6371000

    for shelter in shelters:

        if not shelter.location:
            continue

        lat1 = radians(latitude)
        lon1 = radians(longitude)

        lat2 = radians(
            shelter.location.latitude
        )
        lon2 = radians(
            shelter.location.longitude
        )

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(dlon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        distance = earth_radius * c

        results.append(
            build_shelter_search_result(
                shelter=shelter,
                distance_meters=distance,
            )
        )

    results.sort(
        key=lambda item: (
            item.distance_meters
            if item.distance_meters is not None
            else float("inf")
        )
    )

    return results[:limit]