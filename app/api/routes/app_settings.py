"""Routes for settings management."""
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource
from app.core.exceptions import NotFoundError
from app.repositories.settings_repo import SettingsRepository
from app.schemas.settings import (
    SettingResponse, 
    SettingCreateRequest, 
    SettingUpdateRequest,
    AppSettingsResponse,
    AppSettingsUpdateRequest,
    BulkSettingsRequest
)
from app.models.user import Admin
from app.utils.upload import save_image
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLogAction

router = APIRouter()


@router.get("/public", response_model=ResponseResource[dict])
async def get_public_settings(
    db: AsyncSession = Depends(get_db)
):
    """Get all public settings (no authentication required)."""
    settings_repo = SettingsRepository(db)
    settings_dict = await settings_repo.get_settings_dict(public_only=True)
    
    return ResponseResource.success_response(
        data=settings_dict,
        message="Public settings retrieved successfully"
    )


@router.get("/", response_model=ResponseResource[List[SettingResponse]])
async def get_all_settings(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all settings (admin only)."""
    settings_repo = SettingsRepository(db)
    settings = await settings_repo.get_all_settings(public_only=False)
    
    return ResponseResource.success_response(
        data=[SettingResponse.model_validate(s) for s in settings],
        message="Settings retrieved successfully"
    )


@router.get("/{key}", response_model=ResponseResource[SettingResponse])
async def get_setting(
    key: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific setting by key (admin only)."""
    settings_repo = SettingsRepository(db)
    setting = await settings_repo.get_setting(key)
    
    if not setting:
        raise NotFoundError(resource="Setting", resource_id=key)
    
    return ResponseResource.success_response(
        data=SettingResponse.model_validate(setting),
        message="Setting retrieved successfully"
    )


@router.post("/", response_model=ResponseResource[SettingResponse], status_code=status.HTTP_201_CREATED)
async def create_setting(
    key: str = Form(..., min_length=1, max_length=100),
    value: str = Form(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    is_encrypted: bool = Form(False),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new setting (admin only). Supports key-value pairs."""
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    setting = await settings_repo.set_setting(
        key=key,
        value=value,
        description=description,
        is_public=is_public,
        is_encrypted=is_encrypted
    )
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.CREATE,
        entity_type="settings",
        entity_id=setting.id,
        admin_id=current_admin.id,
        description=f"Setting '{setting.key}' created",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data=SettingResponse.model_validate(setting),
        message="Setting created successfully"
    )


@router.post("/bulk", response_model=ResponseResource[dict], status_code=status.HTTP_201_CREATED)
async def create_bulk_settings(
    settings_data: BulkSettingsRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create or update multiple settings at once (admin only)."""
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    created_count = 0
    updated_count = 0
    
    for key, value in settings_data.settings.items():
        existing = await settings_repo.get_setting(key)
        if existing:
            await settings_repo.set_setting(
                key=key,
                value=value,
                description=settings_data.description,
                is_public=settings_data.is_public if settings_data.is_public is not None else existing.is_public,
                is_encrypted=existing.is_encrypted
            )
            updated_count += 1
        else:
            await settings_repo.set_setting(
                key=key,
                value=value,
                description=settings_data.description,
                is_public=settings_data.is_public if settings_data.is_public is not None else False,
                is_encrypted=False
            )
            created_count += 1
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.CREATE,
        entity_type="settings",
        entity_id=None,
        admin_id=current_admin.id,
        description=f"Bulk settings update: {created_count} created, {updated_count} updated",
        extra_data={"created": created_count, "updated": updated_count, "keys": list(settings_data.settings.keys())},
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data={
            "created": created_count,
            "updated": updated_count,
            "total": len(settings_data.settings)
        },
        message=f"Bulk settings processed: {created_count} created, {updated_count} updated"
    )


@router.put("/{key}", response_model=ResponseResource[SettingResponse])
async def update_setting(
    key: str,
    value: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: Optional[bool] = Form(None),
    is_encrypted: Optional[bool] = Form(None),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a setting (admin only). Supports key-value updates."""
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    existing_setting = await settings_repo.get_setting(key)
    if not existing_setting:
        raise NotFoundError(resource="Setting", resource_id=key)
    
    setting = await settings_repo.set_setting(
        key=key,
        value=value if value is not None else existing_setting.value,
        description=description if description is not None else existing_setting.description,
        is_public=is_public if is_public is not None else existing_setting.is_public,
        is_encrypted=is_encrypted if is_encrypted is not None else existing_setting.is_encrypted
    )
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.SETTINGS_UPDATE,
        entity_type="settings",
        entity_id=setting.id,
        admin_id=current_admin.id,
        description=f"Setting '{setting.key}' updated",
        extra_data={"old_value": existing_setting.value, "new_value": setting.value},
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data=SettingResponse.model_validate(setting),
        message="Setting updated successfully"
    )


@router.get("/app", response_model=ResponseResource[AppSettingsResponse])
async def get_app_settings(
    db: AsyncSession = Depends(get_db)
):
    """Get application settings (logo, email, contact_info, app_name, url)."""
    settings_repo = SettingsRepository(db)
    
    logo = await settings_repo.get_setting_value("logo")
    email = await settings_repo.get_setting_value("email")
    contact_info = await settings_repo.get_setting_value("contact_info")
    app_name = await settings_repo.get_setting_value("app_name")
    url = await settings_repo.get_setting_value("url")
    
    response_data = AppSettingsResponse(
        logo=logo,
        logo_url=f"/uploads/{logo}" if logo else None,
        email=email,
        contact_info=contact_info,
        app_name=app_name,
        url=url
    )
    
    return ResponseResource.success_response(
        data=response_data,
        message="Application settings retrieved successfully"
    )


@router.put("/app", response_model=ResponseResource[AppSettingsResponse])
async def update_app_settings(
    logo: Optional[UploadFile] = File(None),
    email: Optional[str] = Form(None),
    contact_info: Optional[str] = Form(None),
    app_name: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update application settings (admin only). Supports logo image upload."""
    from email_validator import validate_email, EmailNotValidError
    from app.core.exceptions import ValidationError as AppValidationError
    
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    # Handle logo upload
    logo_filename = None
    if logo:
        logo_filename = await save_image(logo)
        await settings_repo.set_setting(
            key="logo",
            value=logo_filename,
            description="Application logo",
            is_public=True
        )
    
    # Update email if provided
    if email:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise AppValidationError("Invalid email format")
        await settings_repo.set_setting(
            key="email",
            value=email,
            description="Application contact email",
            is_public=True
        )
    
    # Update contact_info if provided
    if contact_info is not None:
        await settings_repo.set_setting(
            key="contact_info",
            value=contact_info,
            description="Application contact information",
            is_public=True
        )
    
    # Update app_name if provided
    if app_name is not None:
        await settings_repo.set_setting(
            key="app_name",
            value=app_name,
            description="Application name",
            is_public=True
        )
    
    # Update url if provided
    if url is not None:
        await settings_repo.set_setting(
            key="url",
            value=url,
            description="Application URL",
            is_public=True
        )
    
    # Log the action
    changes = []
    if logo_filename:
        changes.append("logo")
    if email:
        changes.append("email")
    if contact_info is not None:
        changes.append("contact_info")
    if app_name is not None:
        changes.append("app_name")
    if url is not None:
        changes.append("url")
    
    await audit_service.log_action(
        action=AuditLogAction.SETTINGS_UPDATE,
        entity_type="settings",
        entity_id=None,
        admin_id=current_admin.id,
        description=f"Application settings updated: {', '.join(changes)}",
        extra_data={"changed_fields": changes},
        success=True,
        request=None
    )
    
    # Return updated settings
    logo_value = logo_filename if logo_filename else await settings_repo.get_setting_value("logo")
    email_value = email if email else await settings_repo.get_setting_value("email")
    contact_info_value = contact_info if contact_info is not None else await settings_repo.get_setting_value("contact_info")
    app_name_value = app_name if app_name is not None else await settings_repo.get_setting_value("app_name")
    url_value = url if url is not None else await settings_repo.get_setting_value("url")
    
    response_data = AppSettingsResponse(
        logo=logo_value,
        logo_url=f"/uploads/{logo_value}" if logo_value else None,
        email=email_value,
        contact_info=contact_info_value,
        app_name=app_name_value,
        url=url_value
    )
    
    return ResponseResource.success_response(
        data=response_data,
        message="Application settings updated successfully"
    )


@router.delete("/{key}", response_model=ResponseResource[dict])
async def delete_setting(
    key: str,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a setting (admin only)."""
    from app.services.audit_service import AuditService
    from app.models.audit_log import AuditLogAction
    
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    setting = await settings_repo.get_setting(key)
    if not setting:
        raise NotFoundError(resource="Setting", resource_id=key)
    
    deleted = await settings_repo.delete_setting(key)
    
    if deleted:
        # Log the action
        await audit_service.log_action(
            action=AuditLogAction.DELETE,
            entity_type="settings",
            entity_id=setting.id,
            admin_id=current_admin.id,
            description=f"Setting '{key}' deleted",
            success=True,
            request=None
        )
    
    return ResponseResource.success_response(
        data={"deleted": deleted},
        message="Setting deleted successfully" if deleted else "Setting not found"
    )
