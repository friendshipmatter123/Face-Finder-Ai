# ============================================
# FaceFind Backend - Photo Upload & Processing
# ============================================
import numpy as np
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, Event, Photo, FaceEncoding
from schemas import PhotoResponse
from auth import get_current_admin
from face_engine import face_engine
from utils.storage import save_upload_file, delete_file
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/photos", tags=["Photos"])


def process_single_photo(photo_id: str, filepath: str, db_url: str):
    """Background task: Process a single photo for face detection."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            return

        # Get image dimensions
        width, height = face_engine.get_image_dimensions(filepath)
        photo.width = width
        photo.height = height

        # Generate thumbnail
        thumb_path = face_engine.generate_thumbnail(filepath, photo_id)
        if thumb_path:
            photo.thumbnail_path = thumb_path

        # Detect faces and generate encodings
        result = face_engine.process_photo(filepath)

        if result["success"]:
            photo.faces_count = result["faces_count"]
            photo.is_processed = True

            # Save each face encoding
            for i, encoding in enumerate(result["encodings"]):
                loc = result["face_locations"][i] if i < len(result["face_locations"]) else (0, 0, 0, 0)
                face_enc = FaceEncoding(
                    photo_id=photo.id,
                    encoding=encoding.tobytes(),
                    face_location_top=loc[0],
                    face_location_right=loc[1],
                    face_location_bottom=loc[2],
                    face_location_left=loc[3],
                )
                db.add(face_enc)

            # Update event counters
            event = db.query(Event).filter(Event.id == photo.event_id).first()
            if event:
                event.total_faces = (
                    db.query(FaceEncoding)
                    .join(Photo)
                    .filter(Photo.event_id == event.id)
                    .count()
                ) + result["faces_count"]
        else:
            photo.is_processed = True  # Mark processed even if no faces

        db.commit()
        logger.info(f"Processed photo {photo_id}: {result['faces_count']} faces found")

    except Exception as e:
        logger.error(f"Error processing photo {photo_id}: {e}")
        db.rollback()
    finally:
        db.close()


def process_batch_photos(event_id: str, photo_ids: List[str]):
    """Background task: Process a batch of photos."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.processing_status = "processing"
            db.commit()

        for photo_id in photo_ids:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo and not photo.is_processed:
                process_single_photo(photo_id, photo.filepath, "")

        # Update event status
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.processing_status = "completed"
            event.total_photos = db.query(Photo).filter(Photo.event_id == event_id).count()
            event.total_faces = (
                db.query(FaceEncoding)
                .join(Photo)
                .filter(Photo.event_id == event_id)
                .count()
            )
            db.commit()

        logger.info(f"Batch processing completed for event {event_id}")

    except Exception as e:
        logger.error(f"Batch processing error for event {event_id}: {e}")
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.processing_status = "error"
            db.commit()
    finally:
        db.close()


@router.post("/upload/{event_id}", response_model=List[PhotoResponse])
async def upload_photos(
    event_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Upload photos to an event. Processes faces in background."""
    # Verify event ownership
    event = db.query(Event).filter(Event.id == event_id, Event.admin_id == admin.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if len(files) > 500:
        raise HTTPException(status_code=400, detail="Max 500 files per upload batch")

    uploaded_photos = []
    photo_ids = []

    for file in files:
        try:
            file_data = await save_upload_file(file, event_id)
            photo = Photo(
                filename=file_data["filename"],
                original_filename=file_data["original_filename"],
                filepath=file_data["filepath"],
                file_size=file_data["file_size"],
                event_id=event_id,
            )
            db.add(photo)
            db.flush()  # Get the ID before commit
            uploaded_photos.append(photo)
            photo_ids.append(photo.id)
        except ValueError as e:
            logger.warning(f"Skipped file {file.filename}: {e}")
            continue

    if not uploaded_photos:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    # Update event photo count
    event.total_photos += len(uploaded_photos)
    event.processing_status = "processing"
    db.commit()

    # Refresh all photos to get their IDs
    for photo in uploaded_photos:
        db.refresh(photo)

    # Start background processing
    background_tasks.add_task(process_batch_photos, event_id, photo_ids)

    return uploaded_photos


@router.get("/event/{event_id}", response_model=List[PhotoResponse])
async def list_event_photos(
    event_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List photos in an event (paginated)."""
    photos = (
        db.query(Photo)
        .filter(Photo.event_id == event_id)
        .order_by(Photo.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return photos


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: str, db: Session = Depends(get_db)):
    """Get single photo details."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a photo."""
    photo = (
        db.query(Photo)
        .join(Event)
        .filter(Photo.id == photo_id, Event.admin_id == admin.id)
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    delete_file(photo.filepath)
    if photo.thumbnail_path:
        delete_file(photo.thumbnail_path)

    db.delete(photo)
    db.commit()
    return None


@router.get("/processing-status/{event_id}")
async def get_processing_status(event_id: str, db: Session = Depends(get_db)):
    """Check processing status for an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    total = db.query(Photo).filter(Photo.event_id == event_id).count()
    processed = db.query(Photo).filter(
        Photo.event_id == event_id, Photo.is_processed == True
    ).count()

    return {
        "status": event.processing_status,
        "total_photos": total,
        "processed_photos": processed,
        "total_faces": event.total_faces,
        "progress_percent": round((processed / total * 100) if total > 0 else 0, 1),
    }
