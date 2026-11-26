from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging_config import logger

class SSABaseException(Exception):
    """Base class for domain exceptions."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class BarcodeValidationError(SSABaseException):
    """Raised when an invalid barcode format or check-digit is detected."""
    def __init__(self, message: str = "Invalid barcode: must be 8, 12, 13, or 14 digits with valid check digit."):
        super().__init__(message=message, status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422))

class ProductNotFoundError(SSABaseException):
    """Raised when a product cannot be found in local DB or Open Food Facts."""
    def __init__(self, identifier: str):
        super().__init__(
            message=f"Product '{identifier}' not found in local database or Open Food Facts catalog.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ExternalAPIUnavailableError(SSABaseException):
    """Raised when Open Food Facts API times out or fails."""
    def __init__(self, service: str = "Open Food Facts", detail: str = ""):
        msg = f"External service '{service}' is currently unreachable. The product is not cached in the local offline database, and live lookup cannot reach upstream servers. (Offline mode active)."
        if detail:
            msg += f" Details: {detail}"
        super().__init__(message=msg, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

class InsufficientDataError(SSABaseException):
    """Raised when a product lacks essential nutritional parameters for scoring."""
    def __init__(self, message: str = "Insufficient nutritional parameters to compute reliable score."):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class AuthenticationError(SSABaseException):
    """Raised when authentication credentials or token are invalid or expired."""
    def __init__(self, message: str = "Authentication failed or token expired"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(SSABaseException):
    """Raised when user lacks required role/permissions."""
    def __init__(self, message: str = "Access forbidden: insufficient permissions"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)

class ValidationException(SSABaseException):
    """Raised on invalid user or admin inputs."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class DatabaseException(SSABaseException):
    """Raised on database level constraint or execution errors."""
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

async def ssa_domain_exception_handler(request: Request, exc: SSABaseException) -> JSONResponse:
    logger.warning(f"Domain Exception [{exc.status_code}] on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )

async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled Internal Error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected server error occurred. Please contact system administrator.",
            "status_code": 500,
            "path": request.url.path
        }
    )
