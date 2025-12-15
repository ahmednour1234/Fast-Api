"""Token repository for personal access token operations."""
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import PersonalAccessToken, User, Admin


class TokenRepository:
    """Repository for personal access token database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize TokenRepository with database session."""
        self.db = db

    async def create_token(
        self,
        token: str,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> PersonalAccessToken:
        """Create a new personal access token."""
        pat = PersonalAccessToken(
            token=token,
            user_id=user_id,
            admin_id=admin_id,
            name=name,
            expires_at=expires_at
        )
        self.db.add(pat)
        await self.db.commit()
        await self.db.refresh(pat)
        return pat

    async def get_by_token(self, token: str) -> Optional[PersonalAccessToken]:
        """Get token by token string."""
        query = select(PersonalAccessToken).where(PersonalAccessToken.token == token)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, token_id: int) -> Optional[PersonalAccessToken]:
        """Get token by ID."""
        query = select(PersonalAccessToken).where(PersonalAccessToken.id == token_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_tokens(self, user_id: int) -> list[PersonalAccessToken]:
        """Get all tokens for a user."""
        query = select(PersonalAccessToken).where(PersonalAccessToken.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_admin_tokens(self, admin_id: int) -> list[PersonalAccessToken]:
        """Get all tokens for an admin."""
        query = select(PersonalAccessToken).where(PersonalAccessToken.admin_id == admin_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_last_used(self, token: PersonalAccessToken) -> PersonalAccessToken:
        """Update last used timestamp."""
        token.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def delete_token(self, token: PersonalAccessToken) -> None:
        """Delete a token."""
        await self.db.delete(token)
        await self.db.commit()

    async def delete_expired_tokens(self) -> int:
        """Delete all expired tokens. Returns count of deleted tokens."""
        now = datetime.now(timezone.utc)
        query = select(PersonalAccessToken).where(
            PersonalAccessToken.expires_at.isnot(None),
            PersonalAccessToken.expires_at < now
        )
        result = await self.db.execute(query)
        expired_tokens = list(result.scalars().all())
        
        count = len(expired_tokens)
        for token in expired_tokens:
            await self.db.delete(token)
        
        await self.db.commit()
        return count
