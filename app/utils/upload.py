import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import aiofiles

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def save_image(file: UploadFile) -> str:
    """
    Save an uploaded image file and return the filename.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        str: Generated filename (UUID-based)
        
    Raises:
        HTTPException: If file type is invalid or file size exceeds limit
    """
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    # Validate file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_MB}MB"
        )

    # Generate unique filename
    file_ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_ext}"

    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_dir / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    return filename
