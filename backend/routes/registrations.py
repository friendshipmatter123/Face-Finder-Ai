"""Consent-based multi-angle face registration."""
from datetime import datetime
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from database import get_db
from face_engine import face_engine, native_face_lock
from models import FACE_REGISTRATION_ENCODINGS, FACE_REGISTRATIONS

router = APIRouter(prefix="/api/registrations", tags=["Face registration"])


@router.post("/", status_code=201)
async def create_registration(
    front_face: UploadFile = File(...),
    left_face: UploadFile | None = File(default=None),
    right_face: UploadFile | None = File(default=None),
    consent: bool = Form(...),
    db=Depends(get_db),
):
    if not consent:
        raise HTTPException(status_code=400, detail="Consent is required to store facial data.")

    uploads = (("front", front_face), ("left", left_face), ("right", right_face))
    encoded = []
    for angle, upload in uploads:
        if upload is None:
            continue
        image_bytes = await upload.read()
        with native_face_lock:
            encoding, error = face_engine.validate_registration_image(image_bytes)
        if encoding is None:
            suffix = " The front face is required." if angle == "front" else ""
            raise HTTPException(status_code=400, detail=f"{angle.title()} face: {error}{suffix}")
        encoded.append((angle, encoding))

    if not any(angle == "front" for angle, _ in encoded):
        raise HTTPException(status_code=400, detail="A front-face image is required.")

    registration_id = uuid4().hex
    deletion_token = token_urlsafe(32)
    created_at = datetime.utcnow()
    db[FACE_REGISTRATIONS].insert_one({
        "registration_id": registration_id,
        "deletion_token": deletion_token,
        "consent": True,
        "created_at": created_at,
    })
    db[FACE_REGISTRATION_ENCODINGS].insert_many([
        {
            "id": uuid4().hex,
            "registration_id": registration_id,
            "angle": angle,
            "encoding": encoding.tobytes(),
            "created_at": created_at,
        }
        for angle, encoding in encoded
    ])
    return {
        "registration_id": registration_id,
        "deletion_token": deletion_token,
        "angles": [angle for angle, _ in encoded],
    }


@router.delete("/{registration_id}", status_code=204)
async def delete_registration(
    registration_id: str,
    deletion_token: str = Form(...),
    db=Depends(get_db),
):
    registration = db[FACE_REGISTRATIONS].find_one({
        "registration_id": registration_id,
        "deletion_token": deletion_token,
    })
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found or deletion token is invalid.")
    db[FACE_REGISTRATION_ENCODINGS].delete_many({"registration_id": registration_id})
    db[FACE_REGISTRATIONS].delete_one({"registration_id": registration_id})
