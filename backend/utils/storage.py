# ============================================
# FaceFind Backend - Storage Utility
# ============================================
import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
import logging
from config import (
    UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB,
)

logger = logging.getLogger(__name__)

def get_event_upload_dir(event_id: str) -> Path:
    """Get/create upload directory for an event."""
    event_dir = UPLOAD_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    return event_dir


async def save_upload_file(file: UploadFile, event_id: str) -> dict:
    """Save an uploaded file to event directory.
    
    Returns dict with filename, filepath, file_size, and original_filename.
    """
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}")

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    event_dir = get_event_upload_dir(event_id)
    filepath = event_dir / unique_name

    # Stream to disk so a large upload does not require a second full copy in RAM.
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    file_size = 0
    try:
        with open(filepath, "wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise ValueError(f"File too large. Max size: {MAX_FILE_SIZE_MB}MB")
                output.write(chunk)
    except Exception:
        filepath.unlink(missing_ok=True)
        raise

    return {
        "filename": unique_name,
        "filepath": str(filepath),
        "cloudinary_url": None,
        "file_size": file_size,
        "original_filename": file.filename,
    }


def upload_image(filepath: str, folder: str, public_id: str) -> str:
    """Keep generated images on the local filesystem."""
    return filepath


def delete_event_cloudinary_files(event_id: str) -> bool:
    """Compatibility helper; local event files are removed by delete_event_files."""
    return True


def delete_file(filepath: str) -> bool:
    """Delete a file from storage."""
    try:
        if filepath.startswith(("http://", "https://")):
            return True
        path = Path(filepath)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def delete_event_files(event_id: str) -> bool:
    """Delete all files for an event."""
    try:
        event_dir = UPLOAD_DIR / event_id
        if event_dir.exists():
            shutil.rmtree(event_dir)
        return True
    except Exception:
        return False


def get_storage_size_mb() -> float:
    """Get total storage used in MB."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(UPLOAD_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return round(total / (1024 * 1024), 2)
