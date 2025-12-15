from typing import Any, Dict, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class ResponseResource(BaseModel, Generic[T]):
    """Standard API response resource."""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> "ResponseResource[T]":
        """Create a success response."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None) -> "ResponseResource[None]":
        """Create an error response."""
        error = {"code": error_code, "message": message}
        if details:
            error["details"] = details
        return cls(success=False, message=message, error=error)

    @classmethod
    def list_response(cls, items: list[T], message: str = "Success", total: Optional[int] = None) -> "ResponseResource[Dict[str, Any]]":
        """Create a list response."""
        data = {"items": items, "count": len(items)}
        if total is not None:
            data["total"] = total
        return cls(success=True, message=message, data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: list[T]
    total: int
    page: int
    size: int
