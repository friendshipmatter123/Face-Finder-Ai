# ============================================
# FaceFind Backend - Event Routes
# ============================================
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, Event
from schemas import EventCreate, EventUpdate, EventResponse
from auth import get_current_admin
from utils.helpers import generate_event_code
from utils.storage import delete_event_files

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("/", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new event/album."""
    # Generate unique event code
    while True:
        code = generate_event_code()
        existing = db.query(Event).filter(Event.event_code == code).first()
        if not existing:
            break

    event = Event(
        name=data.name,
        description=data.description,
        event_date=data.event_date,
        is_public=data.is_public,
        event_code=code,
        admin_id=admin.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/", response_model=List[EventResponse])
async def list_events(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all events for current admin."""
    events = (
        db.query(Event)
        .filter(Event.admin_id == admin.id)
        .order_by(Event.created_at.desc())
        .all()
    )
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get event details."""
    event = db.query(Event).filter(Event.id == event_id, Event.admin_id == admin.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    data: EventUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update event details."""
    event = db.query(Event).filter(Event.id == event_id, Event.admin_id == admin.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete event and all associated data."""
    event = db.query(Event).filter(Event.id == event_id, Event.admin_id == admin.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Delete files from storage
    delete_event_files(event_id)

    # Delete from database (cascade deletes photos & encodings)
    db.delete(event)
    db.commit()
    return None


@router.get("/code/{event_code}", response_model=EventResponse)
async def get_event_by_code(event_code: str, db: Session = Depends(get_db)):
    """Public endpoint: Get event by event code (for user access)."""
    event = db.query(Event).filter(
        Event.event_code == event_code,
        Event.is_active == True,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or inactive")
    return event
