# ============================================
# FaceFind Backend - Face Search Routes
# ============================================
import time
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models import Event, Photo, FaceEncoding
from schemas import SearchResult, SearchResponse
from face_engine import face_engine
from config import FACE_RECOGNITION_TOLERANCE
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("/{event_code}", response_model=SearchResponse)
async def search_face_in_event(
    event_code: str,
    face_image: UploadFile = File(...),
    tolerance: float = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    🔍 MAIN FEATURE: Search for matching photos by face.
    
    User uploads a selfie/photo → system finds all matching photos in the event.
    """
    start_time = time.time()

    # 1. Find the event
    event = db.query(Event).filter(
        Event.event_code == event_code,
        Event.is_active == True,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or inactive")

    # 2. Read & encode user's face
    image_bytes = await face_image.read()
    user_encoding = face_engine.encode_user_face(image_bytes)

    if user_encoding is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected in the uploaded image. Please upload a clear photo with your face visible.",
        )

    # 3. Get all face encodings for this event
    face_records = (
        db.query(FaceEncoding, Photo)
        .join(Photo)
        .filter(Photo.event_id == event.id)
        .all()
    )

    if not face_records:
        raise HTTPException(
            status_code=404,
            detail="No processed photos found in this event yet. Please wait for processing to complete.",
        )

    # 4. Convert stored encodings to numpy arrays
    known_encodings = []
    encoding_to_photo = []  # Maps encoding index to photo info

    for face_enc, photo in face_records:
        try:
            encoding = np.frombuffer(face_enc.encoding, dtype=np.float64)
            known_encodings.append(encoding)
            encoding_to_photo.append({
                "photo": photo,
                "face_encoding": face_enc,
            })
        except Exception as e:
            logger.warning(f"Failed to decode encoding {face_enc.id}: {e}")
            continue

    # 5. Compare faces
    search_tolerance = tolerance or FACE_RECOGNITION_TOLERANCE
    face_engine_instance = face_engine
    if tolerance and tolerance != FACE_RECOGNITION_TOLERANCE:
        from face_engine import FaceEngine
        face_engine_instance = FaceEngine(tolerance=search_tolerance)

    matches = face_engine_instance.compare_faces(known_encodings, user_encoding)

    # 6. Build results (deduplicate by photo)
    seen_photos = set()
    results = []

    for idx, similarity in matches:
        info = encoding_to_photo[idx]
        photo = info["photo"]
        face_enc = info["face_encoding"]

        if photo.id in seen_photos:
            continue
        seen_photos.add(photo.id)

        results.append(SearchResult(
            photo_id=photo.id,
            filename=photo.filename,
            original_filename=photo.original_filename,
            similarity_score=similarity,
            thumbnail_url=f"/api/files/thumbnail/{photo.id}",
            full_url=f"/api/files/photo/{photo.id}",
            face_location={
                "top": face_enc.face_location_top,
                "right": face_enc.face_location_right,
                "bottom": face_enc.face_location_bottom,
                "left": face_enc.face_location_left,
            },
        ))

    search_time = round(time.time() - start_time, 3)

    logger.info(
        f"Search completed for event '{event.name}': "
        f"{len(results)} matches found in {search_time}s "
        f"(searched {len(known_encodings)} encodings)"
    )

    return SearchResponse(
        total_matches=len(results),
        results=results,
        search_time_seconds=search_time,
    )
