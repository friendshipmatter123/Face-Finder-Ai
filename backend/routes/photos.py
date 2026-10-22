import logging
from datetime import datetime
from uuid import uuid4
from typing import List
import gc
import threading
import tempfile
from pathlib import Path
from urllib.request import urlretrieve
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from schemas import PhotoResponse
from auth import get_current_admin
from database import get_db, database
from models import EVENTS, PHOTOS, FACE_ENCODINGS
from face_engine import face_engine, native_face_lock
from utils.storage import save_upload_file, delete_file, upload_image

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/photos", tags=["Photos"])
_processing_lock = threading.Lock()


def process_single_photo(photo_id: str, filepath: str):
    photo = database[PHOTOS].find_one({"id": photo_id})
    if not photo:
        return
    temporary_path = None
    try:
        if not Path(filepath).exists():
            cloudinary_url = photo.get("filepath", "")
            if cloudinary_url.startswith(("http://", "https://")):
                temporary_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                temporary_path = temporary_file.name
                temporary_file.close()
                urlretrieve(cloudinary_url, temporary_path)
                filepath = temporary_path
            else:
                raise FileNotFoundError(f"Photo file is unavailable: {filepath}")
        width, height = face_engine.get_image_dimensions(filepath)
        thumbnail_path = face_engine.generate_thumbnail(filepath, photo_id)
        with native_face_lock:
            result = face_engine.process_photo(filepath)
        update = {
            "width": width, "height": height,
            "thumbnail_path": thumbnail_path,
            "faces_count": result["faces_count"],
            "is_processed": True,
        }
        database[PHOTOS].update_one({"id": photo_id}, {"$set": update})
        if thumbnail_path:
            update["thumbnail_path"] = upload_image(
                thumbnail_path,
                f"facefind/events/{photo['event_id']}/thumbnails",
                photo_id,
            )
            database[PHOTOS].update_one(
                {"id": photo_id},
                {"$set": {"thumbnail_path": update["thumbnail_path"]}},
            )
        database[FACE_ENCODINGS].delete_many({"photo_id": photo_id})
        if result["success"]:
            records = []
            for index, encoding in enumerate(result["encodings"]):
                location = result["face_locations"][index] if index < len(result["face_locations"]) else (0, 0, 0, 0)
                records.append({
                    "id": uuid4().hex, "photo_id": photo_id, "event_id": photo["event_id"],
                    "encoding": encoding.tobytes(),
                    "face_location": {
                        "top": location[0], "right": location[1],
                        "bottom": location[2], "left": location[3],
                    },
                    "created_at": datetime.utcnow(),
                })
            if records:
                database[FACE_ENCODINGS].insert_many(records)
        logger.info("Processed photo %s: %s faces found", photo_id, result["faces_count"])
    except Exception:
        logger.exception("Error processing photo %s", photo_id)
    finally:
        # face_recognition/OpenCV allocate native buffers that should be released
        # before the next high-resolution photo is decoded.
        width = height = thumbnail_path = result = update = None
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)
        gc.collect()


def process_batch_photos(event_id: str, photo_ids: List[str]):
    # Prevent multiple upload requests from running native face processing
    # concurrently on a small Render instance.
    with _processing_lock:
        database[EVENTS].update_one({"id": event_id}, {"$set": {"processing_status": "processing"}})
        for photo_id in photo_ids:
            photo = database[PHOTOS].find_one({"id": photo_id})
            if photo and not photo.get("is_processed", False):
                process_single_photo(photo_id, photo["local_filepath"])
        database[EVENTS].update_one(
            {"id": event_id},
            {"$set": {
                "processing_status": "completed",
                "total_photos": database[PHOTOS].count_documents({"event_id": event_id}),
                "total_faces": database[FACE_ENCODINGS].count_documents({"event_id": event_id}),
                "updated_at": datetime.utcnow(),
            }},
        )


@router.post("/retry/{event_id}", status_code=202)
async def retry_processing(
    event_id: str,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
    db=Depends(get_db),
):
    event = db[EVENTS].find_one({"id": event_id, "admin_id": admin["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    pending = list(db[PHOTOS].find(
        {"event_id": event_id, "is_processed": {"$ne": True}},
        {"id": 1},
    ))
    if not pending:
        db[EVENTS].update_one(
            {"id": event_id},
            {"$set": {"processing_status": "completed", "updated_at": datetime.utcnow()}},
        )
        return {"message": "All photos are already processed"}
    db[EVENTS].update_one(
        {"id": event_id},
        {"$set": {"processing_status": "processing", "updated_at": datetime.utcnow()}},
    )
    background_tasks.add_task(process_batch_photos, event_id, [photo["id"] for photo in pending])
    return {"message": f"Retry started for {len(pending)} photos"}


@router.post("/upload/{event_id}", response_model=List[PhotoResponse])
async def upload_photos(
    event_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    admin: dict = Depends(get_current_admin),
    db=Depends(get_db),
):
    event = db[EVENTS].find_one({"id": event_id, "admin_id": admin["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if len(files) > 500:
        raise HTTPException(status_code=400, detail="Max 500 files per upload batch")
    uploaded, photo_ids = [], []
    for file in files:
        try:
            file_data = await save_upload_file(file, event_id)
            photo = {
                "id": uuid4().hex, "filename": file_data["filename"],
                "original_filename": file_data["original_filename"],
                "filepath": file_data["filepath"], "thumbnail_path": None,
                "local_filepath": file_data["filepath"],
                "file_size": file_data["file_size"], "width": None, "height": None,
                "faces_count": 0, "is_processed": False, "event_id": event_id,
                "created_at": datetime.utcnow(),
            }
            db[PHOTOS].insert_one(photo)
            if file_data.get("cloudinary_url"):
                db[PHOTOS].update_one(
                    {"id": photo["id"]},
                    {"$set": {"filepath": file_data["cloudinary_url"]}},
                )
                photo["filepath"] = file_data["cloudinary_url"]
            uploaded.append(photo)
            photo_ids.append(photo["id"])
        except ValueError as exc:
            logger.warning("Skipped file %s: %s", file.filename, exc)
    if not uploaded:
        raise HTTPException(status_code=400, detail="No valid files uploaded")
    db[EVENTS].update_one(
        {"id": event_id},
        {"$inc": {"total_photos": len(uploaded)}, "$set": {"processing_status": "processing"}},
    )
    background_tasks.add_task(process_batch_photos, event_id, photo_ids)
    return uploaded


@router.get("/event/{event_id}", response_model=List[PhotoResponse])
async def list_event_photos(event_id: str, skip: int = 0, limit: int = 50, db=Depends(get_db)):
    return list(db[PHOTOS].find({"event_id": event_id}).sort("created_at", -1).skip(skip).limit(limit))


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: str, db=Depends(get_db)):
    photo = db[PHOTOS].find_one({"id": photo_id})
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(photo_id: str, admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    photo = db[PHOTOS].find_one({"id": photo_id})
    event = db[EVENTS].find_one({"id": photo["event_id"], "admin_id": admin["id"]}) if photo else None
    if not photo or not event:
        raise HTTPException(status_code=404, detail="Photo not found")
    delete_file(photo["filepath"])
    if photo.get("thumbnail_path"):
        delete_file(photo["thumbnail_path"])
    db[FACE_ENCODINGS].delete_many({"photo_id": photo_id})
    db[PHOTOS].delete_one({"id": photo_id})


@router.get("/processing-status/{event_id}")
async def get_processing_status(event_id: str, db=Depends(get_db)):
    event = db[EVENTS].find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    total = db[PHOTOS].count_documents({"event_id": event_id})
    processed = db[PHOTOS].count_documents({"event_id": event_id, "is_processed": True})
    return {
        "status": event.get("processing_status", "idle"),
        "total_photos": total, "processed_photos": processed,
        "total_faces": event.get("total_faces", 0),
        "progress_percent": round((processed / total * 100) if total else 0, 1),
    }
