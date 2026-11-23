import gc
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, TEMP_DIR
from face_engine import face_engine, native_face_lock


router = APIRouter(prefix="/api/demo", tags=["Demo"])
SESSION_TTL_SECONDS = 30 * 60
_sessions: Dict[str, dict] = {}
_sessions_lock = threading.Lock()


def _cleanup_expired_sessions():
    now = time.time()
    expired = []
    with _sessions_lock:
        for session_id, session in list(_sessions.items()):
            if now - session["created_at"] > SESSION_TTL_SECONDS:
                expired.append(session_id)
                del _sessions[session_id]
    for session_id in expired:
        shutil.rmtree(TEMP_DIR / "demo" / session_id, ignore_errors=True)


def _validate_file(file: UploadFile):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")


@router.post("/prepare")
async def prepare_demo(files: List[UploadFile] = File(...)):
    _cleanup_expired_sessions()
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Upload at least one demo photo")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Demo mode accepts only 5 photos")

    session_id = uuid.uuid4().hex
    session_dir = TEMP_DIR / "demo" / session_id
    session_dir.mkdir(parents=True, exist_ok=False)
    photos = []
    known_encodings = []
    record_map = []

    try:
        for file in files:
            _validate_file(file)
            photo_id = uuid.uuid4().hex
            ext = Path(file.filename or "").suffix.lower()
            filepath = session_dir / f"{photo_id}{ext}"
            max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            size = 0
            with open(filepath, "wb") as output:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        filepath.unlink(missing_ok=True)
                        raise HTTPException(status_code=400, detail=f"{file.filename} exceeds {MAX_FILE_SIZE_MB}MB")
                    output.write(chunk)

            with native_face_lock:
                result = face_engine.process_photo(str(filepath))
            for index, encoding in enumerate(result["encodings"]):
                known_encodings.append(encoding)
                record_map.append(len(photos))
            photos.append({
                "photo_id": photo_id,
                "filename": filepath.name,
                "original_filename": file.filename,
                "faces_count": result["faces_count"],
                "file_path": str(filepath),
            })

        session = {
            "created_at": time.time(),
            "photos": photos,
            "known_encodings": known_encodings,
            "record_map": record_map,
        }
        with _sessions_lock:
            _sessions[session_id] = session

        return {
            "session_id": session_id,
            "expires_in_seconds": SESSION_TTL_SECONDS,
            "uploaded_photos": len(photos),
            "faces_detected": len(known_encodings),
            "photos": [
                {
                    "photo_id": photo["photo_id"],
                    "original_filename": photo["original_filename"],
                    "faces_count": photo["faces_count"],
                }
                for photo in photos
            ],
        }
    except Exception:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise
    finally:
        gc.collect()


@router.post("/search/{session_id}")
async def search_demo_face(session_id: str, face_image: UploadFile = File(...)):
    _cleanup_expired_sessions()
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Demo session expired or not found")

    image_bytes = await face_image.read()
    with native_face_lock:
        user_encoding = face_engine.encode_user_face(image_bytes)
    if user_encoding is None:
        raise HTTPException(status_code=400, detail="No face detected. Upload a clear photo with your face visible.")

    with native_face_lock:
        matches = face_engine.compare_faces(session["known_encodings"], user_encoding)

    results = []
    seen = set()
    for encoding_index, similarity in matches:
        photo_index = session["record_map"][encoding_index]
        photo = session["photos"][photo_index]
        if photo["photo_id"] in seen:
            continue
        seen.add(photo["photo_id"])
        results.append({
            "photo_id": photo["photo_id"],
            "original_filename": photo["original_filename"],
            "similarity_score": similarity,
            "url": f"/api/demo/file/{session_id}/{photo['photo_id']}",
        })

    return {
        "total_matches": len(results),
        "results": results,
        "privacy": "Processed locally; these photos were not saved to the database or cloud storage.",
    }


@router.get("/file/{session_id}/{photo_id}")
async def get_demo_file(session_id: str, photo_id: str):
    _cleanup_expired_sessions()
    with _sessions_lock:
        session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Demo session expired or not found")
    photo = next((item for item in session["photos"] if item["photo_id"] == photo_id), None)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(photo["file_path"], filename=photo["original_filename"])


@router.delete("/{session_id}")
async def close_demo(session_id: str):
    with _sessions_lock:
        session = _sessions.pop(session_id, None)
    if session:
        shutil.rmtree(TEMP_DIR / "demo" / session_id, ignore_errors=True)
    return {"deleted": True}
