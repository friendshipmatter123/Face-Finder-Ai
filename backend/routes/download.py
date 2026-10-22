# ============================================
# FaceFind Backend - Download & File Serving
# ============================================
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Photo
from utils.helpers import create_zip_from_files
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/files", tags=["Files"])


@router.get("/photo/{photo_id}")
async def serve_photo(photo_id: str, db: Session = Depends(get_db)):
    """Serve a full-resolution photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = Path(photo.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found on disk")

    return FileResponse(
        path=str(filepath),
        filename=photo.original_filename,
        media_type="image/jpeg",
    )


@router.get("/thumbnail/{photo_id}")
async def serve_thumbnail(photo_id: str, db: Session = Depends(get_db)):
    """Serve a photo thumbnail."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # If thumbnail exists, serve it; otherwise serve original
    if photo.thumbnail_path and Path(photo.thumbnail_path).exists():
        return FileResponse(
            path=photo.thumbnail_path,
            media_type="image/jpeg",
        )

    filepath = Path(photo.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(path=str(filepath), media_type="image/jpeg")


@router.post("/download-zip")
async def download_zip(
    photo_ids: List[str],
    db: Session = Depends(get_db),
):
    """Download multiple photos as a ZIP file."""
    if not photo_ids:
        raise HTTPException(status_code=400, detail="No photo IDs provided")

    if len(photo_ids) > 500:
        raise HTTPException(status_code=400, detail="Max 500 photos per download")

    photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
    if not photos:
        raise HTTPException(status_code=404, detail="No photos found")

    filepaths = []
    for photo in photos:
        if Path(photo.filepath).exists():
            filepaths.append(photo.filepath)

    if not filepaths:
        raise HTTPException(status_code=404, detail="No photo files found on disk")

    zip_buffer = create_zip_from_files(filepaths)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=FaceFind_Photos.zip"},
    )


@router.get("/download/{photo_id}")
async def download_single(photo_id: str, db: Session = Depends(get_db)):
    """Download a single photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = Path(photo.filepath)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(
        path=str(filepath),
        filename=photo.original_filename,
        media_type="application/octet-stream",
    )
