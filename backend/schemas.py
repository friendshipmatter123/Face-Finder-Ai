# ============================================
# FaceFind Backend - Pydantic Schemas
# ============================================
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ──── Auth ────
class AdminLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ──── Event ────
class EventCreate(BaseModel):
    name: str
    description: str = ""
    event_date: Optional[datetime] = None
    is_public: bool = False


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class EventResponse(BaseModel):
    id: str
    name: str
    description: str
    event_code: str
    event_date: Optional[datetime]
    is_active: bool
    is_public: bool
    total_photos: int
    total_faces: int
    processing_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──── Photo ────
class PhotoResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    faces_count: int
    is_processed: bool
    event_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ──── Search ────
class SearchResult(BaseModel):
    photo_id: str
    filename: str
    original_filename: str
    similarity_score: float
    thumbnail_url: str
    full_url: str
    face_location: Optional[dict] = None


class SearchResponse(BaseModel):
    total_matches: int
    results: List[SearchResult]
    search_time_seconds: float


# ──── Dashboard Stats ────
class DashboardStats(BaseModel):
    total_events: int
    total_photos: int
    total_faces: int
    active_events: int
    storage_used_mb: float
