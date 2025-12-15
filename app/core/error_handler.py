import traceback
import sys
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppException
from app.core.resources import ResponseResource
from app.core.database import AsyncSessionLocal
from app.repositories.settings_repo import SettingsRepository

# Cache for debug setting to avoid repeated DB calls
_debug_cache = {"enabled": None, "checked": False}


async def is_debug_enabled() -> bool:
    """Check if debug mode is enabled in settings."""
    # Use cache to avoid repeated database calls during error handling
    if _debug_cache["checked"]:
        return _debug_cache["enabled"] or False
    
    try:
        async with AsyncSessionLocal() as session:
            settings_repo = SettingsRepository(session)
            debug_value = await settings_repo.get_setting_value("debug", default="false")
            is_enabled = debug_value.lower() in ("true", "1", "yes", "on")
            _debug_cache["enabled"] = is_enabled
            _debug_cache["checked"] = True
            return is_enabled
    except Exception as e:
        # If we can't check debug setting, default to False for security
        # Log the error for debugging (but don't expose it)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to check debug setting: {str(e)}")
        _debug_cache["enabled"] = False
        _debug_cache["checked"] = True
        return False


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    # Capture traceback immediately
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    traceback_str = "".join(tb_lines)
    
    debug_enabled = await is_debug_enabled()
    
    details = None
    # Add debug information if debug is enabled
    if debug_enabled:
        details = {
            "exception_type": type(exc).__name__,
            "status_code": exc.status_code,
            "traceback": traceback_str
        }
    
    response = ResponseResource.error_response(
        message=str(exc.detail),
        error_code=exc.error_code,
        details=details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    debug_enabled = await is_debug_enabled()
    
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors[field] = error["msg"]
    
    details = errors.copy()
    
    # Add debug information if debug is enabled
    if debug_enabled:
        details["debug"] = {
            "exception_type": type(exc).__name__,
            "raw_errors": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    
    response = ResponseResource.error_response(
        message="Validation error",
        error_code="VALIDATION_ERROR",
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True)
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors."""
    # Capture traceback immediately
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    traceback_str = "".join(tb_lines)
    
    debug_enabled = await is_debug_enabled()
    
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
    
    details = None
    if debug_enabled:
        details = {
            "exception_type": type(exc).__name__,
            "error_message": error_msg,
            "traceback": traceback_str
        }
    
    response = ResponseResource.error_response(
        message=message,
        error_code=error_code,
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.model_dump(exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    # Capture traceback immediately before any async operations
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    traceback_str = "".join(tb_lines)
    
    debug_enabled = await is_debug_enabled()
    
    details = None
    if debug_enabled:
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback_str
        }
    
    # Always log the error server-side for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    response = ResponseResource.error_response(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True)
    )
