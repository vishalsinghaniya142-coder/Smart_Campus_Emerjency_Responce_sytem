from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app: FastAPI) -> None:
    """
    Configure Cross-Origin Resource Sharing (CORS)
    for the FastAPI application.
    """

    app.add_middleware(
        CORSMiddleware,

        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",

            "http://localhost:5173",
            "http://127.0.0.1:5173",

            "http://localhost:5500",
            "http://127.0.0.1:5500",

            "http://localhost:5501",
            "http://127.0.0.1:5501",
        ],

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],
    )