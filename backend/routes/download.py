from typing import List
from pathlib import Path
from urllib.request import urlretrieve
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from database import get_db
from models import PHOTOS
from config import TEMP_DIR
from utils.helpers import create_zip_from_files

router = APIRouter(prefix="/api/files", tags=["Files"])


def require_photo(photo_id: str, db):
    photo = db[PHOTOS].find_one({"id": photo_id})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("/photo/{photo_id}")
async def serve_photo(photo_id: str, db=Depends(get_db)):
    photo = require_photo(photo_id, db)
    if photo["filepath"].startswith(("http://", "https://")):
        return RedirectResponse(photo["filepath"])
    filepath = Path(photo["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found on disk")
    return FileResponse(path=str(filepath), filename=photo["original_filename"], media_type="image/jpeg")


@router.get("/thumbnail/{photo_id}")
async def serve_thumbnail(photo_id: str, db=Depends(get_db)):
    photo = require_photo(photo_id, db)
    if photo.get("thumbnail_path", "").startswith(("http://", "https://")):
        return RedirectResponse(photo["thumbnail_path"])
    path = Path(photo["thumbnail_path"]) if photo.get("thumbnail_path") else Path(photo["filepath"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(path=str(path), media_type="image/jpeg")


@router.post("/download-zip")
async def download_zip(photo_ids: List[str], db=Depends(get_db)):
    if not photo_ids or len(photo_ids) > 500:
        raise HTTPException(status_code=400, detail="Provide between 1 and 500 photo IDs")
    photos = list(db[PHOTOS].find({"id": {"$in": photo_ids}}))
    temporary_paths = []
    filepaths = []
    for photo in photos:
        filepath = photo["filepath"]
        if filepath.startswith(("http://", "https://")):
            temporary_path = TEMP_DIR / f"{uuid4().hex}.jpg"
            urlretrieve(filepath, temporary_path)
            temporary_paths.append(temporary_path)
            filepaths.append(str(temporary_path))
        elif Path(filepath).exists():
            filepaths.append(filepath)
    if not filepaths:
        raise HTTPException(status_code=404, detail="No photo files found on disk")
    try:
        response = StreamingResponse(
            create_zip_from_files(filepaths),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=FaceFind_Photos.zip"},
        )
        return response
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)


@router.get("/download/{photo_id}")
async def download_single(photo_id: str, db=Depends(get_db)):
    photo = require_photo(photo_id, db)
    if photo["filepath"].startswith(("http://", "https://")):
        return RedirectResponse(photo["filepath"])
    filepath = Path(photo["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(path=str(filepath), filename=photo["original_filename"], media_type="application/octet-stream")
