from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.resources import ResponseResource
from app.core.exceptions import NotFoundError, ForbiddenError
from app.schemas.user import UserResponse, UserUpdateRequest
from app.models.user import User
from app.services.user_service import UserService
from app.utils.upload import save_image

router = APIRouter()


@router.get("/me", response_model=ResponseResource[UserResponse])
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    response_data = UserResponse.model_validate(current_user)
    if current_user.avatar:
        response_data.avatar_url = f"/uploads/{current_user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User profile retrieved successfully"
    )


@router.put("/me", response_model=ResponseResource[UserResponse])
async def update_my_profile(
    name: Optional[str] = Form(None, max_length=100),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None, max_length=20),
    password: Optional[str] = Form(None, min_length=6),
    avatar: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    from pydantic import EmailStr
    from app.core.exceptions import ValidationError as AppValidationError
    
    # Validate email format if provided
    if email:
        try:
            EmailStr._validate(email, None)
        except Exception:
            raise AppValidationError("Invalid email format")
    
    user_service = UserService(db)
    
    # Handle avatar upload if provided
    avatar_filename = None
    if avatar:
        avatar_filename = await save_image(avatar)
    
    updated_user = await user_service.update_user(
        user=current_user,
        name=name,
        email=email,
        phone=phone,
        password=password,
        avatar=avatar_filename
    )
    
    response_data = UserResponse.model_validate(updated_user)
    if updated_user.avatar:
        response_data.avatar_url = f"/uploads/{updated_user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Profile updated successfully"
    )


@router.delete("/me", response_model=ResponseResource[dict])
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user's account (soft delete)."""
    user_service = UserService(db)
    await user_service.soft_delete_user(current_user)
    
    return ResponseResource.success_response(
        data={"deleted": True},
        message="Account deleted successfully"
    )
