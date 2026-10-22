from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import AdminCreate, AdminLogin, AdminResponse, Token, DashboardStats
from auth import hash_password, verify_password, create_access_token, get_current_admin
from database import get_db
from models import ADMINS, EVENTS, PHOTOS, FACE_ENCODINGS
from utils.storage import get_storage_size_mb

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.post("/login", response_model=Token)
async def admin_login(data: AdminLogin, db=Depends(get_db)):
    admin = db[ADMINS].find_one({"email": data.email})
    if not admin or not verify_password(data.password, admin["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not admin.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return {"access_token": create_access_token({"sub": admin["id"], "email": admin["email"]}), "token_type": "bearer"}


@router.post("/register", response_model=AdminResponse, status_code=201)
async def admin_register(data: AdminCreate, db=Depends(get_db)):
    if db[ADMINS].find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    admin = {
        "id": uuid4().hex, "email": data.email,
        "hashed_password": hash_password(data.password), "name": data.name,
        "is_active": True, "created_at": datetime.utcnow(),
    }
    db[ADMINS].insert_one(admin)
    return admin


@router.get("/me", response_model=AdminResponse)
async def get_me(admin: dict = Depends(get_current_admin)):
    return admin


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(admin: dict = Depends(get_current_admin), db=Depends(get_db)):
    event_filter = {"admin_id": admin["id"]}
    event_ids = [e["id"] for e in db[EVENTS].find(event_filter, {"id": 1})]
    return DashboardStats(
        total_events=db[EVENTS].count_documents(event_filter),
        total_photos=db[PHOTOS].count_documents({"event_id": {"$in": event_ids}}),
        total_faces=db[FACE_ENCODINGS].count_documents({"event_id": {"$in": event_ids}}),
        active_events=db[EVENTS].count_documents({**event_filter, "is_active": True}),
        storage_used_mb=get_storage_size_mb(),
    )
