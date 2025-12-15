"""Repository for collection operations."""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection


class CollectionRepository:
    """Repository for collection database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_collection_by_id(self, collection_id: int, include_deleted: bool = False) -> Optional[Collection]:
        """Get collection by ID."""
        query = select(Collection).where(Collection.id == collection_id)
        if not include_deleted:
            query = query.where(Collection.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_collection_by_slug(self, slug: str, include_deleted: bool = False) -> Optional[Collection]:
        """Get collection by slug."""
        query = select(Collection).where(Collection.slug == slug)
        if not include_deleted:
            query = query.where(Collection.deleted_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_collections(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Collection], int]:
        """Get all collections with pagination."""
        query = select(Collection)
        if not include_deleted:
            query = query.where(Collection.deleted_at.is_(None))
        if is_active is not None:
            query = query.where(Collection.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(Collection)
        if not include_deleted:
            count_query = count_query.where(Collection.deleted_at.is_(None))
        if is_active is not None:
            count_query = count_query.where(Collection.is_active == is_active)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Collection.sort_order, Collection.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        collections = result.scalars().all()
        
        return list(collections), total

    async def create_collection(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        image: Optional[str] = None,
        is_active: bool = True,
        sort_order: int = 0,
        created_by_admin_id: Optional[int] = None
    ) -> Collection:
        """Create a new collection."""
        collection = Collection(
            name=name,
            slug=slug,
            description=description,
            image=image,
            is_active=is_active,
            sort_order=sort_order,
            created_by_admin_id=created_by_admin_id
        )
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def update_collection(
        self,
        collection: Collection,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_order: Optional[int] = None
    ) -> Collection:
        """Update a collection."""
        if name is not None:
            collection.name = name
        if slug is not None:
            collection.slug = slug
        if description is not None:
            collection.description = description
        if image is not None:
            collection.image = image
        if is_active is not None:
            collection.is_active = is_active
        if sort_order is not None:
            collection.sort_order = sort_order
        
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def soft_delete_collection(self, collection: Collection) -> Collection:
        """Soft delete a collection."""
        collection.soft_delete()
        await self.db.commit()
        await self.db.refresh(collection)
        return collection

    async def restore_collection(self, collection: Collection) -> Collection:
        """Restore a soft deleted collection."""
        collection.restore()
        await self.db.commit()
        await self.db.refresh(collection)
        return collection