from fastapi import FastAPI
import logging

from app.core.config import settings
from app.db.database import initialize_firebase  # ensures Firebase is initialized at startup
from app.api.v1 import auth, sync, backup, entities, social, media, devices, ai, user, reviews, admin, study, finance
from app.core.rate_limit import setup_rate_limiting

from fastapi.middleware.cors import CORSMiddleware

# Basic logging setup for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_rate_limiting(app)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(backup.router, prefix="/api/v1/backup", tags=["backup"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(media.router, prefix="/api/v1/media", tags=["media"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(study.router, prefix="/api/v1/study", tags=["study"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["finance"])


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "application": settings.PROJECT_NAME,
        "status": "running",
    }


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    import firebase_admin
    firebase_status = "initialized" if firebase_admin._apps else "not initialized"
    return {
        "status": "healthy",
        "firebase": firebase_status,
    }