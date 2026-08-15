from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings

from app.services.auth_service import configure_user_repository
from app.services.database.users import FirebaseUserRepository

from app.middleware.cors import configure_cors
from app.middleware.error_handler import (
    register_exception_handlers,
)
from app.middleware.auth_middleware import (
    configure_authentication_middleware,
)

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.incidents import router as incidents_router
from app.routes.alerts import router as alerts_router
from app.routes.sos import router as sos_router
from app.routes.shelters import router as shelters_router
from app.routes.predictions import router as predictions_router
from app.routes.chatbot import router as chatbot_router
from app.routes.image_analysis import (
    router as image_analysis_router,
)


# ============================================================
# APPLICATION CONSTANTS
# ============================================================

APP_TITLE = settings.APP_NAME

APP_VERSION = settings.APP_VERSION

APP_DESCRIPTION = """
Smart Campus Emergency Response System Backend API.

This backend acts as the central API layer between the
frontend and the different system services.

Main responsibilities:

- Authentication
- User management
- Emergency incidents
- Emergency alerts
- SOS
- Shelter APIs
- AI prediction APIs
- AI chatbot APIs
- Emergency image-analysis APIs

Architecture:

Frontend
    |
    | REST API / JSON / Multipart
    v
FastAPI Backend
    |
    +------------------+
    |                  |
    v                  v
Authentication       Business APIs
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
            AI        Maps       Firebase
             |           |           |
             +-----------+-----------+
                         |
                         v
                     Response
                         |
                         v
                     Frontend
"""


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Startup:
        Runs when the FastAPI server starts.

    Shutdown:
        Runs when the FastAPI server stops.

    External services such as Firebase, Gemini and Maps
    should be initialized through their own service/integration
    layers rather than placing their implementation directly
    inside main.py.
    """

    # --------------------------------------------------------
    # STARTUP
    # --------------------------------------------------------

    print("=" * 70)
    print(
        "Starting Smart Campus Emergency Response System"
    )
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Version: {APP_VERSION}")
    print("=" * 70)

    print("Loading application configuration...")
    print("Loading middleware...")
    print("Loading database...")


# ========================================================
# FIREBASE / USER REPOSITORY
# ========================================================

    try:
        user_repository = FirebaseUserRepository()

        configure_user_repository(
        user_repository
                        )

        print("Firebase user repository configured.")

    except Exception as exc:
        print(
        f"Firebase user repository configuration failed: {exc}"
        )
        raise


    print("Loading API routes...")
    print("Backend startup completed.")

# --------------------------------------------------------
# APPLICATION RUNNING
# --------------------------------------------------------

    yield

# --------------------------------------------------------
# SHUTDOWN
# --------------------------------------------------------

print("=" * 70)
print(
    "Shutting down Smart Campus Emergency Response System"
    )
print("=" * 70)

print("Backend shutdown completed.")


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================
# REGISTER EXCEPTION HANDLERS
# ============================================================
#
# Error handlers are registered at application level.
#
# Flow:
#
# Request
#    |
#    v
# Route / Middleware
#    |
#    v
# Exception
#    |
#    v
# error_handler.py
#    |
#    v
# response.py
#    |
#    v
# Standard JSON response
#
# ============================================================

register_exception_handlers(
    app
)


# ============================================================
# REGISTER CORS
# ============================================================
#
# Frontend and backend normally run on different origins
# during development.
#
# Example:
#
# Frontend:
#     http://localhost:5500
#
# Backend:
#     http://127.0.0.1:8000
#
# cors.py reads the allowed origins from config.py.
#
# ============================================================

configure_cors(
    app
)


# ============================================================
# REGISTER AUTHENTICATION MIDDLEWARE
# ============================================================
#
# This middleware:
#
# 1. Identifies public endpoints.
# 2. Reads Authorization header.
# 3. Extracts Bearer JWT.
# 4. Verifies JWT.
# 5. Stores authentication information in request.state.
#
# Actual JWT cryptographic logic remains inside:
#
#     app/utils/jwt_handler.py
#
# Route-level authentication remains available through:
#
#     app/dependencies.py
#
# ============================================================

configure_authentication_middleware(
    app
)


# ============================================================
# REGISTER AUTHENTICATION ROUTES
# ============================================================
#
# POST /auth/register
# POST /auth/login
#
# ============================================================

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER USER ROUTES
# ============================================================
#
# GET /users/profile
#
# ============================================================

app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)


# ============================================================
# REGISTER INCIDENT ROUTES
# ============================================================
#
# POST /incidents
# GET /incidents
# GET /incidents/{incident_id}
#
# ============================================================

app.include_router(
    incidents_router,
    prefix="/incidents",
    tags=["Incidents"],
)


# ============================================================
# REGISTER ALERT ROUTES
# ============================================================
#
# GET /alerts
# POST /alerts
#
# ============================================================

app.include_router(
    alerts_router,
    prefix="/alerts",
    tags=["Alerts"],
)


# ============================================================
# REGISTER SOS ROUTES
# ============================================================
#
# POST /sos
#
# ============================================================

app.include_router(
    sos_router,
    prefix="/sos",
    tags=["SOS"],
)


# ============================================================
# REGISTER SHELTER ROUTES
# ============================================================
#
# GET /shelters
# GET /shelters/nearest
#
# Maps / nearest-shelter implementation will stay in the
# service/integration layer rather than inside main.py.
#
# ============================================================

app.include_router(
    shelters_router,
    prefix="/shelters",
    tags=["Shelters"],
)


# ============================================================
# REGISTER AI PREDICTION ROUTES
# ============================================================
#
# POST /prediction
#
# The actual AI implementation is NOT placed here.
#
# Backend route
#      |
#      v
# AI integration
#      |
#      v
# Member 3 AI module
#
# ============================================================

app.include_router(
    predictions_router,
    prefix="/prediction",
    tags=["AI Prediction"],
)


# ============================================================
# REGISTER AI CHATBOT ROUTES
# ============================================================
#
# POST /chatbot
#
# ============================================================

app.include_router(
    chatbot_router,
    prefix="/chatbot",
    tags=["AI Chatbot"],
)


# ============================================================
# REGISTER IMAGE ANALYSIS ROUTES
# ============================================================
#
# POST /image-analysis
#
# Frontend sends multipart image.
#
# Backend receives image.
# Backend route passes it to AI integration.
# Member 3 handles actual AI/vision implementation.
#
# ============================================================

app.include_router(
    image_analysis_router,
    prefix="/image-analysis",
    tags=["Image Analysis"],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["System"],
)
async def root():
    """
    Root endpoint.

    Used to verify that the API application is running.
    """

    return {
        "success": True,
        "status": "success",
        "message": (
            "Smart Campus Emergency Response "
            "System API is running."
        ),
        "data": {
            "application": APP_TITLE,
            "version": APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "documentation": "/docs",
            "redoc": "/redoc",
        },
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["System"],
)
async def health_check():
    """
    Basic backend health check.

    At this stage this checks the FastAPI application itself.

    Later this can be expanded to check:
        - Firebase
        - AI service
        - Maps service
        - notification service
    """

    return {
        "success": True,
        "status": "healthy",
        "message": "Backend is healthy.",
        "data": {
            "application": APP_TITLE,
            "version": APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get(
    "/api-info",
    tags=["System"],
)
async def api_info():
    """
    Return high-level information about available API areas.

    This endpoint is useful during development and integration
    testing.

    It does not replace the Swagger documentation.
    """

    return {
        "success": True,
        "status": "success",
        "message": "API information fetched successfully.",
        "data": {
            "authentication": [
                "POST /auth/register",
                "POST /auth/login",
            ],
            "users": [
                "GET /users/profile",
            ],
            "incidents": [
                "POST /incidents",
                "GET /incidents",
                "GET /incidents/{incident_id}",
            ],
            "sos": [
                "POST /sos",
            ],
            "alerts": [
                "GET /alerts",
                "POST /alerts",
            ],
            "shelters": [
                "GET /shelters",
                "GET /shelters/nearest",
            ],
            "ai": [
                "POST /prediction",
                "POST /chatbot",
                "POST /image-analysis",
            ],
        },
    }


# ============================================================
# APPLICATION CONFIGURATION VALIDATION
# ============================================================

def validate_application_configuration() -> None:
    """
    Validate the backend configuration.

    This function is intentionally kept separate from the
    route definitions so configuration validation can later
    be expanded without modifying the API endpoints.
    """

    settings.validate()


# ============================================================
# RUNNING THIS FILE DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    validate_application_configuration()

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )