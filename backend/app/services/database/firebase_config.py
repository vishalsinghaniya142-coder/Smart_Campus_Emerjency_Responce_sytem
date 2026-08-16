import os
from pathlib import Path

import firebase_admin

from firebase_admin import credentials


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

CREDENTIALS_DIR = BASE_DIR / "credentials"


# ============================================================
# FIREBASE INITIALIZATION
# ============================================================

def initialize_firebase():

    if firebase_admin._apps:

        return firebase_admin.get_app()


    # --------------------------------------------------------
    # OPTION 1:
    # SERVICE ACCOUNT JSON
    # --------------------------------------------------------

    credential_path = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "",
    ).strip()


    if credential_path:

        path = Path(
            credential_path
        )

        if not path.is_absolute():

            path = BASE_DIR / path

        if not path.exists():

            raise FileNotFoundError(
                f"Firebase credential file not found: {path}"
            )

        cred = credentials.Certificate(
            str(path)
        )

        return firebase_admin.initialize_app(
            cred
        )


    # --------------------------------------------------------
    # OPTION 2:
    # credentials/*.json
    # --------------------------------------------------------

    json_files = list(
        CREDENTIALS_DIR.glob("*.json")
    )


    if len(json_files) == 0:

        raise FileNotFoundError(
            "Firebase service-account JSON was not found. "
            "Place the JSON file inside backend/credentials/ "
            "or configure FIREBASE_CREDENTIALS_PATH."
        )


    if len(json_files) > 1:

        raise RuntimeError(
            "Multiple Firebase service-account JSON files found. "
            "Keep only one Firebase service-account JSON file."
        )


    credential_file = json_files[0]


    cred = credentials.Certificate(
        str(credential_file)
    )


    return firebase_admin.initialize_app(
        cred
    )


# ============================================================
# FIREBASE APP
# ============================================================

def get_firebase_app():

    return initialize_firebase()