"""Repository for settings operations."""
from typing import Optional, List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import Setting


class SettingsRepository:
    """Repository for settings database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setting(self, key: str) -> Optional[Setting]:
        """Get a setting by key."""
        query = select(Setting).where(Setting.key == key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_setting_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting value by key, returns default if not found."""
        setting = await self.get_setting(key)
        return setting.value if setting else default

    async def set_setting(
        self,
        key: str,
        value: str,
        description: Optional[str] = None,
        is_public: bool = False,
        is_encrypted: bool = False
    ) -> Setting:
        """Create or update a setting."""
        from datetime import datetime, timezone
        
        setting = await self.get_setting(key)
        
        if setting:
            # Update existing
            setting.value = value
            if description is not None:
                setting.description = description
            setting.is_public = is_public
            setting.is_encrypted = is_encrypted
            setting.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            setting = Setting(
                key=key,
                value=value,
                description=description,
                is_public=is_public,
                is_encrypted=is_encrypted
            )
            self.db.add(setting)
        
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete_setting(self, key: str) -> bool:
        """Delete a setting by key."""
        setting = await self.get_setting(key)
        if setting:
            await self.db.delete(setting)
            await self.db.commit()
            return True
        return False

    async def get_all_settings(self, public_only: bool = False) -> List[Setting]:
        """Get all settings."""
        query = select(Setting)
        if public_only:
            query = query.where(Setting.is_public == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_settings_dict(self, public_only: bool = False) -> Dict[str, str]:
        """Get all settings as a dictionary."""
        settings = await self.get_all_settings(public_only=public_only)
        return {setting.key: setting.value for setting in settings}
