from datetime import datetime
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ADMINS, EVENTS, PHOTOS, FACE_ENCODINGS
from schemas import EventCreate, EventUpdate, EventResponse
from auth import get_current_admin
from utils.helpers import generate_event_code
from utils.storage import delete_event_files, delete_event_cloudinary_files

router = APIRouter(prefix="/api/events", tags=["Events"])


def event_document(data, admin_id: str, code: str) -> dict:
    now = datetime.utcnow()
    return {
        "id": uuid4().hex, "name": data.name, "description": data.description,
        "event_date": data.event_date, "is_public": data.is_public,
        "event_code": code, "admin_id": admin_id, "is_active": True,
        "total_photos": 0, "total_faces": 0, "processing_status": "idle",
        "created_at": now, "updated_at": now,
    }


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(data: EventCreate, admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    code = generate_event_code()
    while db[EVENTS].find_one({"event_code": code}):
        code = generate_event_code()
    event = event_document(data, admin["id"], code)
    db[EVENTS].insert_one(event)
    return event


@router.get("/", response_model=List[EventResponse])
async def list_events(admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    return list(db[EVENTS].find({"admin_id": admin["id"]}).sort("created_at", -1))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    event = db[EVENTS].find_one({"id": event_id, "admin_id": admin["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, data: EventUpdate, admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    event = db[EVENTS].find_one({"id": event_id, "admin_id": admin["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    updates = data.model_dump(exclude_unset=True)
    if updates:
        updates["updated_at"] = datetime.utcnow()
        db[EVENTS].update_one({"id": event_id}, {"$set": updates})
    return db[EVENTS].find_one({"id": event_id})


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str, admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    event = db[EVENTS].find_one({"id": event_id, "admin_id": admin["id"]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    delete_event_files(event_id)
    if not delete_event_cloudinary_files(event_id):
        raise HTTPException(
            status_code=502,
            detail="Event database records were not deleted because Cloudinary cleanup failed",
        )
    db[FACE_ENCODINGS].delete_many({"event_id": event_id})
    db[PHOTOS].delete_many({"event_id": event_id})
    db[EVENTS].delete_one({"id": event_id})


@router.get("/code/{event_code}", response_model=EventResponse)
async def get_event_by_code(event_code: str, db=Depends(get_db)):
    event = db[EVENTS].find_one({"event_code": event_code, "is_active": True})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or inactive")
    return event
