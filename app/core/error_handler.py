from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppException
from app.core.resources import ResponseResource


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    error_data = {
        "code": exc.error_code or "APPLICATION_ERROR",
        "message": str(exc.detail)
    }
    
    response = ResponseResource.error_response(
        message=str(exc.detail),
        error_code=exc.error_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors[field] = error["msg"]
    
    response = ResponseResource.error_response(
        message="Validation error",
        error_code="VALIDATION_ERROR",
        details=errors
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True)
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else "Database integrity error"
    
    # Check for common integrity errors
    if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
        message = "Resource already exists"
        error_code = "DUPLICATE_ENTRY"
    elif "foreign key" in error_msg.lower():
        message = "Referenced resource does not exist"
        error_code = "FOREIGN_KEY_VIOLATION"
    else:
        message = "Database integrity error"
        error_code = "INTEGRITY_ERROR"
    
    response = ResponseResource.error_response(
        message=message,
        error_code=error_code
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    response = ResponseResource.error_response(
        message="Internal server error",
        error_code="INTERNAL_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True)
    )
