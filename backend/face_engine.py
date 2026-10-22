# ============================================
# FaceFind Backend - Face Recognition Engine
# ============================================
import numpy as np
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("⚠️  face_recognition not available - using DEMO mode")
    
import cv2
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Optional
from config import (
    FACE_RECOGNITION_TOLERANCE, FACE_RECOGNITION_MODEL, THUMBNAIL_SIZE,
    THUMBNAIL_DIR, MAX_PROCESSING_DIM,
)
import logging
import time
import threading

logger = logging.getLogger(__name__)
native_face_lock = threading.Lock()


class FaceEngine:
    """Core AI engine for face detection, encoding, and matching."""

    def __init__(self, tolerance: float = None, model: str = None):
        self.tolerance = tolerance or FACE_RECOGNITION_TOLERANCE
        self.model = model or FACE_RECOGNITION_MODEL
        logger.info(f"FaceEngine initialized | tolerance={self.tolerance} | model={self.model}")

    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image from path for face_recognition processing."""
        try:
            if FACE_REC_AVAILABLE:
                image = face_recognition.load_image_file(image_path)
                return self._resize_for_processing(image)
            else:
                # Use OpenCV as fallback
                img_cv = cv2.imread(str(image_path))
                if img_cv is None:
                    return None
                img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                return self._resize_for_processing(img_rgb)
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

    def load_image_from_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Load image from bytes (for uploaded files)."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_cv is None:
                return None
            # Convert BGR to RGB (face_recognition uses RGB)
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            return self._resize_for_processing(img_rgb)
        except Exception as e:
            logger.error(f"Failed to load image from bytes: {e}")
            return None

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect face locations in an image.
        
        Returns list of (top, right, bottom, left) tuples.
        """
        if not FACE_REC_AVAILABLE:
            # DEMO MODE: Use OpenCV Haar Cascade for basic face detection
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                # Convert from (x, y, w, h) to (top, right, bottom, left)
                face_locations = []
                for (x, y, w, h) in faces:
                    face_locations.append((y, x+w, y+h, x))
                return face_locations
            except Exception as e:
                logger.error(f"OpenCV face detection failed: {e}")
                return []
        
        try:
            face_locations = face_recognition.face_locations(image, model=self.model)
            return face_locations
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []

    def encode_faces(
        self, image: np.ndarray, face_locations: List[Tuple] = None
    ) -> List[np.ndarray]:
        """Generate 128-dimensional face encodings.
        
        If face_locations is None, will detect faces first.
        """
        if not FACE_REC_AVAILABLE:
            # DEMO MODE: Generate random 128-D vectors as placeholder encodings
            if face_locations is None:
                face_locations = self.detect_faces(image)
            if not face_locations:
                return []
            # Return random encodings for demo
            return [np.random.rand(128).astype(np.float64) for _ in face_locations]
        
        try:
            if face_locations is None:
                face_locations = self.detect_faces(image)
            
            if not face_locations:
                return []

            encodings = face_recognition.face_encodings(image, face_locations)
            return encodings
        except Exception as e:
            logger.error(f"Face encoding failed: {e}")
            return []

    def process_photo(self, image_path: str) -> dict:
        """Process a single photo: detect faces, generate encodings.
        
        Returns dict with face_locations, encodings, and count.
        """
        result = {
            "face_locations": [],
            "encodings": [],
            "faces_count": 0,
            "success": False,
            "error": None,
        }

        image = self.load_image(image_path)
        if image is None:
            result["error"] = "Failed to load image"
            return result

        face_locations = self.detect_faces(image)
        if not face_locations:
            result["success"] = True  # No faces is not an error
            return result

        encodings = self.encode_faces(image, face_locations)

        result["face_locations"] = face_locations
        result["encodings"] = encodings
        result["faces_count"] = len(encodings)
        result["success"] = True

        return result

    def encode_user_face(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Encode a user's uploaded/captured face photo.
        
        Returns the first face encoding found, or None.
        """
        image = self.load_image_from_bytes(image_bytes)
        if image is None:
            return None

        face_locations = self.detect_faces(image)
        if not face_locations:
            return None

        encodings = self.encode_faces(image, face_locations)
        if not encodings:
            return None

        # Return the largest face (most likely the main subject)
        if len(face_locations) > 1:
            areas = [(b - t) * (r - l) for (t, r, b, l) in face_locations]
            largest_idx = np.argmax(areas)
            return encodings[largest_idx]

        return encodings[0]

    def compare_faces(
        self,
        known_encodings: List[np.ndarray],
        user_encoding: np.ndarray,
    ) -> List[Tuple[int, float]]:
        """Compare user encoding against known encodings.
        
        Returns list of (index, distance) for matches within tolerance.
        Lower distance = better match.
        """
        if not known_encodings:
            return []

        if not FACE_REC_AVAILABLE:
            # DEMO MODE: Use Euclidean distance for comparison
            distances = np.array([
                np.linalg.norm(encoding - user_encoding)
                for encoding in known_encodings
            ])
        else:
            distances = face_recognition.face_distance(known_encodings, user_encoding)
        
        matches = []

        for idx, distance in enumerate(distances):
            if distance <= self.tolerance:
                similarity = round(1.0 - distance, 4)  # Convert distance to similarity
                matches.append((idx, similarity))

        # Sort by similarity descending (best matches first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    @staticmethod
    def _resize_for_processing(image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        largest_dimension = max(height, width)
        if largest_dimension <= MAX_PROCESSING_DIM:
            return image
        scale = MAX_PROCESSING_DIM / largest_dimension
        return cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    def generate_thumbnail(self, image_path: str, photo_id: str) -> Optional[str]:
        """Generate a thumbnail for the image."""
        try:
            thumb_path = THUMBNAIL_DIR / f"{photo_id}.jpg"
            with Image.open(image_path) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(str(thumb_path), "JPEG", quality=85)
            return str(thumb_path)
        except Exception as e:
            logger.error(f"Thumbnail generation failed for {image_path}: {e}")
            return None

    def get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        """Get image width and height."""
        try:
            with Image.open(image_path) as img:
                return img.size  # (width, height)
        except Exception:
            return (0, 0)


# Singleton instance
face_engine = FaceEngine()
