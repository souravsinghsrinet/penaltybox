import os
import shutil
from fastapi import UploadFile
from datetime import datetime
import uuid

UPLOAD_DIR = "uploads/proofs"

def ensure_upload_dir():
    """Ensure the upload directory exists"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_upload_file(file: UploadFile) -> str:
    """
    Save an uploaded file and return its relative path
    """
    ensure_upload_dir()
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{timestamp}_{unique_id}{file_extension}"
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return f"/{file_path}"  # Return relative path

def remove_file(file_path: str) -> bool:
    """
    Remove a file given its relative path
    Returns True if successful, False otherwise
    """
    # Remove leading slash if present
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
