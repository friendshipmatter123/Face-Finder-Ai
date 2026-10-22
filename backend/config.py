# ============================================
# FaceFind Backend - Configuration
# ============================================
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
THUMBNAIL_DIR = BASE_DIR / "thumbnails"
TEMP_DIR = BASE_DIR / "temp"

# Create directories
for d in [UPLOAD_DIR, THUMBNAIL_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "facefind")

# Cloudinary object storage
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# JWT Auth
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-key-set-SECRET_KEY-in-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Face Recognition
FACE_RECOGNITION_TOLERANCE = float(os.getenv("FACE_TOLERANCE", "0.5"))  # Lower = stricter
FACE_RECOGNITION_MODEL = os.getenv("FACE_MODEL", "hog")  # "hog" (CPU) or "cnn" (GPU)

# Upload limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_BULK_UPLOAD = int(os.getenv("MAX_BULK_UPLOAD", "500"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Thumbnail size
THUMBNAIL_SIZE = (300, 300)

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# Default admin credentials
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@facefind.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
