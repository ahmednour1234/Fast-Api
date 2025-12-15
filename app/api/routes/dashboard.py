"""Routes for dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.core.resources import ResponseResource
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import DashboardStatisticsResponse
from app.models.user import Admin

router = APIRouter()


@router.get("/statistics", response_model=ResponseResource[DashboardStatisticsResponse])
async def get_dashboard_statistics(
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics (admin only)."""
    dashboard_service = DashboardService(db)
    statistics = await dashboard_service.get_statistics()
    
    return ResponseResource.success_response(
        data=statistics,
        message="Dashboard statistics retrieved successfully"
    )