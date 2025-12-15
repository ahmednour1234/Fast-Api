"""Routes for settings management."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource
from app.core.exceptions import NotFoundError
from app.repositories.settings_repo import SettingsRepository
from app.schemas.settings import SettingResponse, SettingCreateRequest, SettingUpdateRequest
from app.models.user import Admin

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
    setting_data: SettingCreateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new setting (admin only)."""
    from app.services.audit_service import AuditService
    
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    setting = await settings_repo.set_setting(
        key=setting_data.key,
        value=setting_data.value,
        description=setting_data.description,
        is_public=setting_data.is_public,
        is_encrypted=setting_data.is_encrypted
    )
    
    # Log the action
    await audit_service.log_action(
        action="create",
        entity_type="settings",
        entity_id=setting.id,
        admin_id=current_admin.id,
        description=f"Setting '{setting.key}' created",
        success=True
    )
    
    return ResponseResource.success_response(
        data=SettingResponse.model_validate(setting),
        message="Setting created successfully"
    )


@router.put("/{key}", response_model=ResponseResource[SettingResponse])
async def update_setting(
    key: str,
    setting_data: SettingUpdateRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a setting (admin only)."""
    from app.services.audit_service import AuditService
    from app.models.audit_log import AuditLogAction
    
    settings_repo = SettingsRepository(db)
    audit_service = AuditService(db)
    
    existing_setting = await settings_repo.get_setting(key)
    if not existing_setting:
        raise NotFoundError(resource="Setting", resource_id=key)
    
    # Update setting
    update_data = {}
    if setting_data.value is not None:
        update_data["value"] = setting_data.value
    if setting_data.description is not None:
        update_data["description"] = setting_data.description
    if setting_data.is_public is not None:
        update_data["is_public"] = setting_data.is_public
    if setting_data.is_encrypted is not None:
        update_data["is_encrypted"] = setting_data.is_encrypted
    
    setting = await settings_repo.set_setting(
        key=key,
        value=update_data.get("value", existing_setting.value),
        description=update_data.get("description", existing_setting.description),
        is_public=update_data.get("is_public", existing_setting.is_public),
        is_encrypted=update_data.get("is_encrypted", existing_setting.is_encrypted)
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
