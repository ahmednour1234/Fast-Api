"""Tests for upload utilities."""
import pytest
from io import BytesIO
from unittest.mock import MagicMock
from fastapi import UploadFile

from app.utils.upload import save_image
from app.core.config import settings


class TestUploadUtils:
    """Test cases for upload utilities."""
    
    @pytest.mark.asyncio
    async def test_save_image_jpeg(self, tmp_path, monkeypatch):
        """Test saving JPEG image."""
        # Mock UPLOAD_DIR to use tmp_path
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
        
        # Create a fake image file
        image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Minimal JPEG header
        file = UploadFile(
            filename="test.jpg",
            file=BytesIO(image_data * 1000)  # Make it larger
        )
        # Mock content_type property
        type(file).content_type = property(lambda self: "image/jpeg")
        
        filename = await save_image(file)
        
        assert filename is not None
        assert filename.endswith(".jpg")
        assert (tmp_path / filename).exists()
    
    @pytest.mark.asyncio
    async def test_save_image_png(self, tmp_path, monkeypatch):
        """Test saving PNG image."""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
        
        # Create a fake PNG file
        image_data = b'\x89PNG\r\n\x1a\n'  # PNG header
        file = UploadFile(
            filename="test.png",
            file=BytesIO(image_data * 1000)
        )
        type(file).content_type = property(lambda self: "image/png")
        
        filename = await save_image(file)
        
        assert filename is not None
        assert filename.endswith(".png")
    
    @pytest.mark.asyncio
    async def test_save_image_invalid_type(self, tmp_path, monkeypatch):
        """Test saving invalid file type."""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
        
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"not an image")
        )
        type(file).content_type = property(lambda self: "text/plain")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await save_image(file)
    
    @pytest.mark.asyncio
    async def test_save_image_too_large(self, tmp_path, monkeypatch):
        """Test saving file that's too large."""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)  # 1MB limit
        
        # Create a large file (2MB)
        large_data = b'\xff\xd8\xff\xe0' * (1024 * 1024)  # ~2MB
        file = UploadFile(
            filename="large.jpg",
            file=BytesIO(large_data)
        )
        type(file).content_type = property(lambda self: "image/jpeg")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await save_image(file)
