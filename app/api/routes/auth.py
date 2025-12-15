from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from starlette.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import EmailStr

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.core.resources import ResponseResource
from app.core.exceptions import ValidationError as AppValidationError
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=ResponseResource[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(..., min_length=3, max_length=50),
    name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(...),  # Email validation will be done manually
    password: str = Form(..., min_length=6),
    phone: Optional[str] = Form(None, max_length=20),
    avatar: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    # Validate email format using email-validator
    try:
        from email_validator import validate_email, EmailNotValidError
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        raise AppValidationError("Invalid email format")
    
    auth_service = AuthService(db)
    user = await auth_service.register(
        username=username,
        name=name,
        email=email,
        password=password,
        phone=phone,
        avatar=avatar
    )
    
    # Build response with avatar_url
    response_data = UserResponse.model_validate(user)
    if user.avatar:
        response_data.avatar_url = f"/uploads/{user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User registered successfully"
    )


@router.post("/login", response_model=ResponseResource[TokenResponse])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,  # FastAPI will inject this automatically
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token. Can use username or email as identifier."""
    auth_service = AuthService(db)
    token = await auth_service.login(form_data.username, form_data.password, request)
    
    token_response = TokenResponse(access_token=token)
    return ResponseResource.success_response(
        data=token_response,
        message="Login successful"
    )
