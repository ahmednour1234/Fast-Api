"""Schemas for dashboard."""
from pydantic import BaseModel


class DashboardStatisticsResponse(BaseModel):
    """Dashboard statistics response schema."""
    users: dict
    admins: dict
    collections: dict
    logins: dict