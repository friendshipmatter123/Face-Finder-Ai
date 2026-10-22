# ============================================
# FaceFind Backend - Helper Utilities
# ============================================
import random
import string
import zipfile
import io
from pathlib import Path
from typing import List


def generate_event_code(length: int = 8) -> str:
    """Generate a unique alphanumeric event code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def create_zip_from_files(filepaths: List[str]) -> io.BytesIO:
    """Create a ZIP archive from list of file paths.
    
    Returns BytesIO buffer containing the ZIP file.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath in filepaths:
            path = Path(filepath)
            if path.exists():
                zf.write(path, arcname=path.name)
    zip_buffer.seek(0)
    return zip_buffer


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
