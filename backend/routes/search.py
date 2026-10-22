import time
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from schemas import SearchResult, SearchResponse
from database import get_db
from models import EVENTS, PHOTOS, FACE_ENCODINGS
from face_engine import face_engine, native_face_lock
from config import FACE_RECOGNITION_TOLERANCE

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("/{event_code}", response_model=SearchResponse)
async def search_face_in_event(
    event_code: str,
    face_image: UploadFile = File(...),
    tolerance: float = Form(default=None),
    db=Depends(get_db),
):
    start_time = time.time()
    event = db[EVENTS].find_one({"event_code": event_code, "is_active": True})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or inactive")
    image_bytes = await face_image.read()
    with native_face_lock:
        user_encoding = face_engine.encode_user_face(image_bytes)
    if user_encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in the uploaded image. Please upload a clear photo with your face visible.")

    records = list(db[FACE_ENCODINGS].find({"event_id": event["id"]}))
    if not records:
        raise HTTPException(status_code=404, detail="No processed photos found in this event yet. Please wait for processing to complete.")
    known_encodings, record_map = [], []
    for record in records:
        try:
            known_encodings.append(np.frombuffer(record["encoding"], dtype=np.float64))
            record_map.append(record)
        except (TypeError, ValueError):
            continue
    search_tolerance = tolerance or FACE_RECOGNITION_TOLERANCE
    engine = face_engine if search_tolerance == FACE_RECOGNITION_TOLERANCE else __import__("face_engine").FaceEngine(tolerance=search_tolerance)
    with native_face_lock:
        matches = engine.compare_faces(known_encodings, user_encoding)
    results, seen = [], set()
    for idx, similarity in matches:
        record = record_map[idx]
        photo_id = record["photo_id"]
        if photo_id in seen:
            continue
        photo = db[PHOTOS].find_one({"id": photo_id})
        if not photo:
            continue
        seen.add(photo_id)
        results.append(SearchResult(
            photo_id=photo_id, filename=photo["filename"],
            original_filename=photo["original_filename"], similarity_score=similarity,
            thumbnail_url=f"/api/files/thumbnail/{photo_id}",
            full_url=f"/api/files/photo/{photo_id}",
            face_location=record.get("face_location"),
        ))
    return SearchResponse(total_matches=len(results), results=results, search_time_seconds=round(time.time() - start_time, 3))
