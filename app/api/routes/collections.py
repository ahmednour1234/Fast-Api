"""Routes for collection management."""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import re

from app.core.database import get_db
from app.api.deps import get_current_admin, require_permission
from app.core.resources import ResponseResource, PaginatedResponse
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.repositories.collection_repo import CollectionRepository
from app.schemas.collection import CollectionResponse, CollectionCreateRequest, CollectionUpdateRequest
from app.models.user import Admin
from app.utils.upload import save_image
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLogAction

router = APIRouter()


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


@router.get("/", response_model=ResponseResource[PaginatedResponse[CollectionResponse]])
async def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all collections with pagination (admin only)."""
    collection_repo = CollectionRepository(db)
    collections, total = await collection_repo.get_all_collections(
        skip=skip,
        limit=limit,
        is_active=is_active
    )
    
    collection_responses = []
    for collection in collections:
        response_data = CollectionResponse.model_validate(collection)
        if collection.image:
            response_data.image_url = f"/uploads/{collection.image}"
        collection_responses.append(response_data)
    
    return ResponseResource.success_response(
        data=PaginatedResponse(
            items=collection_responses,
            total=total,
            page=skip // limit + 1,
            size=len(collection_responses)
        ),
        message="Collections retrieved successfully"
    )


@router.get("/{collection_id}", response_model=ResponseResource[CollectionResponse])
async def get_collection(
    collection_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific collection by ID (admin only)."""
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_collection_by_id(collection_id)
    
    if not collection:
        raise NotFoundError(resource="Collection", resource_id=collection_id)
    
    response_data = CollectionResponse.model_validate(collection)
    if collection.image:
        response_data.image_url = f"/uploads/{collection.image}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Collection retrieved successfully"
    )


@router.post("/", response_model=ResponseResource[CollectionResponse], status_code=status.HTTP_201_CREATED)
async def create_collection(
    name: str = Form(..., min_length=1, max_length=200),
    slug: Optional[str] = Form(None, max_length=200),
    description: Optional[str] = Form(None),
    is_active: bool = Form(True),
    sort_order: int = Form(0),
    image: Optional[UploadFile] = File(None),
    current_admin: Admin = Depends(require_permission("collections", "create")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new collection (admin only, requires permission)."""
    collection_repo = CollectionRepository(db)
    audit_service = AuditService(db)
    
    # Generate slug if not provided
    if not slug:
        slug = slugify(name)
    
    # Check if slug already exists
    existing = await collection_repo.get_collection_by_slug(slug)
    if existing:
        raise ConflictError(f"Collection with slug '{slug}' already exists")
    
    # Handle image upload
    image_filename = None
    if image:
        image_filename = await save_image(image)
    
    collection = await collection_repo.create_collection(
        name=name,
        slug=slug,
        description=description,
        image=image_filename,
        is_active=is_active,
        sort_order=sort_order,
        created_by_admin_id=current_admin.id
    )
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.CREATE,
        entity_type="collection",
        entity_id=collection.id,
        admin_id=current_admin.id,
        description=f"Collection '{collection.name}' created",
        success=True,
        request=None
    )
    
    response_data = CollectionResponse.model_validate(collection)
    if collection.image:
        response_data.image_url = f"/uploads/{collection.image}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Collection created successfully"
    )


@router.put("/{collection_id}", response_model=ResponseResource[CollectionResponse])
async def update_collection(
    collection_id: int,
    name: Optional[str] = Form(None, min_length=1, max_length=200),
    slug: Optional[str] = Form(None, max_length=200),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    sort_order: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_admin: Admin = Depends(require_permission("collections", "update")),
    db: AsyncSession = Depends(get_db)
):
    """Update a collection (admin only, requires permission)."""
    collection_repo = CollectionRepository(db)
    audit_service = AuditService(db)
    
    collection = await collection_repo.get_collection_by_id(collection_id)
    if not collection:
        raise NotFoundError(resource="Collection", resource_id=collection_id)
    
    # Check slug uniqueness if slug is being updated
    if slug and slug != collection.slug:
        existing = await collection_repo.get_collection_by_slug(slug)
        if existing:
            raise ConflictError(f"Collection with slug '{slug}' already exists")
    
    # Handle image upload
    image_filename = None
    if image:
        image_filename = await save_image(image)
    
    updated_collection = await collection_repo.update_collection(
        collection=collection,
        name=name,
        slug=slug,
        description=description,
        image=image_filename,
        is_active=is_active,
        sort_order=sort_order
    )
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.UPDATE,
        entity_type="collection",
        entity_id=updated_collection.id,
        admin_id=current_admin.id,
        description=f"Collection '{updated_collection.name}' updated",
        success=True,
        request=None
    )
    
    response_data = CollectionResponse.model_validate(updated_collection)
    if updated_collection.image:
        response_data.image_url = f"/uploads/{updated_collection.image}"
    
    return ResponseResource.success_response(
        data=response_data,
        message="Collection updated successfully"
    )


@router.delete("/{collection_id}", response_model=ResponseResource[dict])
async def delete_collection(
    collection_id: int,
    current_admin: Admin = Depends(require_permission("collections", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a collection (admin only, requires permission)."""
    collection_repo = CollectionRepository(db)
    audit_service = AuditService(db)
    
    collection = await collection_repo.get_collection_by_id(collection_id)
    if not collection:
        raise NotFoundError(resource="Collection", resource_id=collection_id)
    
    await collection_repo.soft_delete_collection(collection)
    
    # Log the action
    await audit_service.log_action(
        action=AuditLogAction.SOFT_DELETE,
        entity_type="collection",
        entity_id=collection.id,
        admin_id=current_admin.id,
        description=f"Collection '{collection.name}' deleted",
        success=True,
        request=None
    )
    
    return ResponseResource.success_response(
        data={"deleted": True},
        message="Collection deleted successfully"
    )
