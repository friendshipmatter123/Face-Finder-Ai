from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from database import get_db
from models import PHOTOS
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
    filepath = Path(photo["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found on disk")
    return FileResponse(path=str(filepath), filename=photo["original_filename"], media_type="image/jpeg")


@router.get("/thumbnail/{photo_id}")
async def serve_thumbnail(photo_id: str, db=Depends(get_db)):
    photo = require_photo(photo_id, db)
    path = Path(photo["thumbnail_path"]) if photo.get("thumbnail_path") else Path(photo["filepath"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(path=str(path), media_type="image/jpeg")


@router.post("/download-zip")
async def download_zip(photo_ids: List[str], db=Depends(get_db)):
    if not photo_ids or len(photo_ids) > 500:
        raise HTTPException(status_code=400, detail="Provide between 1 and 500 photo IDs")
    photos = list(db[PHOTOS].find({"id": {"$in": photo_ids}}))
    filepaths = [photo["filepath"] for photo in photos if Path(photo["filepath"]).exists()]
    if not filepaths:
        raise HTTPException(status_code=404, detail="No photo files found on disk")
    return StreamingResponse(
        create_zip_from_files(filepaths),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=FaceFind_Photos.zip"},
    )


@router.get("/download/{photo_id}")
async def download_single(photo_id: str, db=Depends(get_db)):
    photo = require_photo(photo_id, db)
    filepath = Path(photo["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Photo file not found")
    return FileResponse(path=str(filepath), filename=photo["original_filename"], media_type="application/octet-stream")
