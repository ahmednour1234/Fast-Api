from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from starlette.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import EmailStr, ValidationError

from app.core.database import get_db
from app.services.admin_auth_service import AdminAuthService
from app.core.resources import ResponseResource
from app.core.exceptions import ValidationError as AppValidationError
from app.schemas.auth import TokenResponse
from app.schemas.admin import AdminResponse

router = APIRouter()


@router.post("/register", response_model=ResponseResource[AdminResponse], status_code=status.HTTP_201_CREATED)
async def register_admin(
    username: str = Form(..., min_length=3, max_length=50),
    name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(...),
    password: str = Form(..., min_length=6),
    phone: Optional[str] = Form(None, max_length=20),
    avatar: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Register a new admin (admin only - should be protected in production)."""
    # Validate email format using email-validator
    try:
        from email_validator import validate_email, EmailNotValidError
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        raise AppValidationError("Invalid email format")
    
    admin_auth_service = AdminAuthService(db)
    admin = await admin_auth_service.register(
        username=username,
        name=name,
        email=email,
        password=password,
        phone=phone,
        avatar=avatar
    )
    
    # Build response with avatar_url
    response_data = AdminResponse.model_validate(admin)
    if admin.avatar:
        response_data.avatar_url = f"/uploads/{admin.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Admin registered successfully"
    )


@router.post("/login", response_model=ResponseResource[TokenResponse])
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Admin login and get access token. Can use username or email as identifier."""
    admin_auth_service = AdminAuthService(db)
    token = await admin_auth_service.login(form_data.username, form_data.password, request)
    
    token_response = TokenResponse(access_token=token)
    return ResponseResource.success_response(
        data=token_response,
        message="Admin login successful"
    )
