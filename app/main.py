from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine
from app.api.v1 import auth, sync, backup, entities, social, media, devices, ai, user, reviews, admin
from app.core.rate_limit import setup_rate_limiting
import logging
import json
import firebase_admin
from firebase_admin import credentials

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

if settings.FIREBASE_CREDENTIALS_JSON:
    try:
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        logging.info("Firebase Admin initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Firebase Admin: {e}")

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

@app.get("/")
def root():
    return {
        "application": settings.PROJECT_NAME,
        "status": "running",
    }

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "Connected"
        }

    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "Database connection failed"
        }