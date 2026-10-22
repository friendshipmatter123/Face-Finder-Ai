# ============================================
# FaceFind Backend - SQLAlchemy Models
# ============================================
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    ForeignKey, Text, LargeBinary
)
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Admin(Base):
    __tablename__ = "admins"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), default="Admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="admin", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    event_code = Column(String(20), unique=True, nullable=False, index=True)
    event_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    admin_id = Column(String, ForeignKey("admins.id"), nullable=False)
    total_photos = Column(Integer, default=0)
    total_faces = Column(Integer, default=0)
    processing_status = Column(String(50), default="idle")  # idle, processing, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = relationship("Admin", back_populates="events")
    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    thumbnail_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, default=0)  # in bytes
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    faces_count = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="photos")
    face_encodings = relationship("FaceEncoding", back_populates="photo", cascade="all, delete-orphan")


class FaceEncoding(Base):
    __tablename__ = "face_encodings"

    id = Column(String, primary_key=True, default=generate_uuid)
    photo_id = Column(String, ForeignKey("photos.id"), nullable=False)
    encoding = Column(LargeBinary, nullable=False)  # numpy array as bytes
    face_location_top = Column(Integer, nullable=True)
    face_location_right = Column(Integer, nullable=True)
    face_location_bottom = Column(Integer, nullable=True)
    face_location_left = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    photo = relationship("Photo", back_populates="face_encodings")
