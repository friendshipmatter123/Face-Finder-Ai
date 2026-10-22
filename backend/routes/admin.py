# ============================================
# FaceFind Backend - Admin Routes
# ============================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Admin, Event, Photo, FaceEncoding
from schemas import AdminCreate, AdminLogin, AdminResponse, Token, DashboardStats
from auth import hash_password, verify_password, create_access_token, get_current_admin
from utils.storage import get_storage_size_mb

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/login", response_model=Token)
async def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login → returns JWT token."""
    admin = db.query(Admin).filter(Admin.email == data.email).first()
    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": admin.id, "email": admin.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=AdminResponse, status_code=201)
async def admin_register(data: AdminCreate, db: Session = Depends(get_db)):
    """Register a new admin."""
    existing = db.query(Admin).filter(Admin.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = Admin(
        email=data.email,
        hashed_password=hash_password(data.password),
        name=data.name,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.get("/me", response_model=AdminResponse)
async def get_me(admin: Admin = Depends(get_current_admin)):
    """Get current admin profile."""
    return admin


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get admin dashboard statistics."""
    total_events = db.query(Event).filter(Event.admin_id == admin.id).count()
    active_events = db.query(Event).filter(
        Event.admin_id == admin.id, Event.is_active == True
    ).count()
    total_photos = (
        db.query(Photo)
        .join(Event)
        .filter(Event.admin_id == admin.id)
        .count()
    )
    total_faces = (
        db.query(FaceEncoding)
        .join(Photo)
        .join(Event)
        .filter(Event.admin_id == admin.id)
        .count()
    )
    storage = get_storage_size_mb()

    return DashboardStats(
        total_events=total_events,
        total_photos=total_photos,
        total_faces=total_faces,
        active_events=active_events,
        storage_used_mb=storage,
    )
