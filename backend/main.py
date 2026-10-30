"""FaceFind FastAPI application."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db, close_db
from auth import hash_password
from config import (
    CORS_ORIGINS, HOST, PORT, DEBUG,
    DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD,
    UPLOAD_DIR, THUMBNAIL_DIR,
)
from models import ADMINS, EVENTS
from database import database
from routes import admin, events, photos, search, download, registrations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("FaceFind")

app = FastAPI(
    title="FaceFind API",
    description="AI-Powered Face Recognition Photo Search Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/thumbnails", StaticFiles(directory=str(THUMBNAIL_DIR)), name="thumbnails")

app.include_router(admin.router)
app.include_router(events.router)
app.include_router(photos.router)
app.include_router(search.router)
app.include_router(download.router)
app.include_router(registrations.router)


@app.on_event("startup")
async def startup():
    logger.info("FaceFind starting up...")
    init_db()
    # BackgroundTasks are in-process; a Render restart terminates them.
    # Release stale processing flags so the admin can retry safely.
    reset_result = database[EVENTS].update_many(
        {"processing_status": "processing"},
        {"$set": {"processing_status": "idle", "updated_at": __import__("datetime").datetime.utcnow()}},
    )
    if reset_result.modified_count:
        logger.warning("Reset %s stale processing event(s) after startup", reset_result.modified_count)
    existing = database[ADMINS].find_one({"email": DEFAULT_ADMIN_EMAIL})
    if not existing:
        database[ADMINS].insert_one({
            "id": __import__("uuid").uuid4().hex,
            "email": DEFAULT_ADMIN_EMAIL,
            "hashed_password": hash_password(DEFAULT_ADMIN_PASSWORD),
            "name": "FaceFind Admin",
            "is_active": True,
            "created_at": __import__("datetime").datetime.utcnow(),
        })
        logger.info("Default admin created: %s", DEFAULT_ADMIN_EMAIL)
    logger.info("FaceFind is ready")


@app.on_event("shutdown")
async def shutdown():
    close_db()


@app.get("/")
async def root():
    return {"app": "FaceFind", "version": "1.0.0", "docs": "/docs", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
