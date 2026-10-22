# ============================================
# 🔍 FaceFind - Main FastAPI Application
# ============================================
# AI-Powered Face Recognition Photo Search
# ============================================
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db, SessionLocal
from models import Admin
from auth import hash_password
from config import (
    CORS_ORIGINS, HOST, PORT, DEBUG,
    DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD,
    UPLOAD_DIR, THUMBNAIL_DIR,
)
from routes import admin, events, photos, search, download

# ──── Logging ────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("FaceFind")

# ──── App ────
app = FastAPI(
    title="FaceFind API",
    description="AI-Powered Face Recognition Photo Search Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ──── CORS ────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──── Static Files ────
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/thumbnails", StaticFiles(directory=str(THUMBNAIL_DIR)), name="thumbnails")

# ──── Routes ────
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(photos.router)
app.include_router(search.router)
app.include_router(download.router)


# ──── Startup ────
@app.on_event("startup")
async def startup():
    logger.info("🚀 FaceFind starting up...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Create default admin if not exists
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == DEFAULT_ADMIN_EMAIL).first()
        if not existing:
            default_admin = Admin(
                email=DEFAULT_ADMIN_EMAIL,
                hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
                name="FaceFind Admin",
            )
            db.add(default_admin)
            db.commit()
            logger.info(f"✅ Default admin created: {DEFAULT_ADMIN_EMAIL}")
        else:
            logger.info(f"✅ Admin exists: {DEFAULT_ADMIN_EMAIL}")
    finally:
        db.close()

    logger.info("🔍 FaceFind is ready!")


# ──── Root ────
@app.get("/")
async def root():
    return {
        "app": "FaceFind",
        "version": "1.0.0",
        "description": "AI-Powered Face Recognition Photo Search",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ──── Run ────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
