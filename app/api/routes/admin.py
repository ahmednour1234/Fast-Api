from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource
from app.core.exceptions import NotFoundError
from app.schemas.user import UserResponse
from app.schemas.admin import AdminResponse
from app.models.user import User, Admin
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from app.utils.upload import save_image

router = APIRouter()


@router.get("/me", response_model=ResponseResource[AdminResponse])
async def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    """Get current admin's profile."""
    response_data = AdminResponse.model_validate(current_admin)
    if current_admin.avatar:
        response_data.avatar_url = f"/uploads/{current_admin.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Admin profile retrieved successfully"
    )


@router.get("/users", response_model=ResponseResource[dict])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_deleted: bool = Query(False),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)."""
    user_service = UserService(db)
    users, total = await user_service.get_all_users(
        skip=skip,
        limit=limit,
        include_deleted=include_deleted
    )
    
    user_list = []
    for user in users:
        user_data = UserResponse.model_validate(user)
        if user.avatar:
            user_data.avatar_url = f"/uploads/{user.avatar}"
        user_list.append(user_data)
    
    return ResponseResource.list_response(
        items=user_list,
        message="Users retrieved successfully",
        total=total
    )


@router.get("/users/{user_id}", response_model=ResponseResource[UserResponse])
async def get_user_by_id(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID (admin only)."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id, include_deleted=True)
    
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)
    
    response_data = UserResponse.model_validate(user)
    if user.avatar:
        response_data.avatar_url = f"/uploads/{user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User retrieved successfully"
    )


@router.put("/users/{user_id}", response_model=ResponseResource[UserResponse])
async def update_user(
    user_id: int,
    request: Request,
    name: Optional[str] = Form(None, max_length=100),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None, max_length=20),
    password: Optional[str] = Form(None, min_length=6),
    is_active: Optional[bool] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a user (admin only)."""
    from app.core.exceptions import ValidationError as AppValidationError
    
    # Validate email format if provided
    if email:
        try:
            from email_validator import validate_email, EmailNotValidError
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise AppValidationError("Invalid email format")
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id, include_deleted=False)
    
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)
    
    # Handle avatar upload if provided
    avatar_filename = None
    if avatar:
        avatar_filename = await save_image(avatar)
    
    updated_user = await user_service.update_user(
        user=user,
        name=name,
        email=email,
        phone=phone,
        password=password,
        avatar=avatar_filename,
        is_active=is_active
    )
    
    # Log the action
    from app.services.audit_service import AuditService
    from app.models.audit_log import AuditLogAction
    
    audit_service = AuditService(db)
    changes = []
    if name is not None:
        changes.append("name")
    if email is not None:
        changes.append("email")
    if phone is not None:
        changes.append("phone")
    if password is not None:
        changes.append("password")
    if is_active is not None:
        changes.append("is_active")
    if avatar_filename is not None:
        changes.append("avatar")
    
    await audit_service.log_action(
        action=AuditLogAction.UPDATE,
        entity_type="user",
        entity_id=updated_user.id,
        admin_id=current_admin.id,
        description=f"User '{updated_user.username}' updated by admin '{current_admin.username}'",
        extra_data={"changed_fields": changes},
        success=True,
        request=request
    )
    
    response_data = UserResponse.model_validate(updated_user)
    if updated_user.avatar:
        response_data.avatar_url = f"/uploads/{updated_user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User updated successfully"
    )


@router.patch("/users/{user_id}/activate", response_model=ResponseResource[UserResponse])
async def activate_user(
    user_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activate a user (admin only)."""
    from app.services.audit_service import AuditService
    from app.models.audit_log import AuditLogAction
    
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = await user_service.get_user_by_id(user_id, include_deleted=False)
    
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)
    
    user = await user_service.activate_user(user)
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.ACTIVATE,
        entity_type="user",
        entity_id=user.id,
        admin_id=current_admin.id,
        description=f"User '{user.username}' activated by admin '{current_admin.username}'",
        success=True,
        request=request
    )
    
    response_data = UserResponse.model_validate(user)
    if user.avatar:
        response_data.avatar_url = f"/uploads/{user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User activated successfully"
    )


@router.patch("/users/{user_id}/block", response_model=ResponseResource[UserResponse])
async def block_user(
    user_id: int,
    request: Request,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Block a user (admin only)."""
    from app.services.audit_service import AuditService
    from app.models.audit_log import AuditLogAction
    
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = await user_service.get_user_by_id(user_id, include_deleted=False)
    
    if not user:
        raise NotFoundError(resource="User", resource_id=user_id)
    
    user = await user_service.deactivate_user(user)
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.BLOCK,
        entity_type="user",
        entity_id=user.id,
        admin_id=current_admin.id,
        description=f"User '{user.username}' blocked by admin '{current_admin.username}'",
        success=True,
        request=request
    )
    
    response_data = UserResponse.model_validate(user)
    if user.avatar:
        response_data.avatar_url = f"/uploads/{user.avatar}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="User blocked successfully"
    )
