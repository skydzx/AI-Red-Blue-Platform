"""Custom exceptions for AI Red Blue Platform."""

from typing import Optional, Any

import structlog


class PlatformException(Exception):
    """Base exception for all platform exceptions."""

    def __init__(
        self,
        message: str,
        details: Optional[dict] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.code = code or "PLATFORM_ERROR"

    def __str__(self) -> str:
        """Return string representation."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class ConfigurationException(PlatformException):
    """Exception raised for configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key


class ValidationException(PlatformException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, code="VALIDATION_ERROR", details=details, **kwargs)
        self.field = field
        self.value = value


class AuthenticationException(PlatformException):
    """Exception raised for authentication errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs,
    ):
        super().__init__(message, code="AUTH_ERROR", **kwargs)


class AuthorizationException(PlatformException):
    """Exception raised for authorization errors."""

    def __init__(
        self,
        message: str = "Access denied",
        required_permissions: Optional[list] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if required_permissions:
            details["required_permissions"] = required_permissions
        super().__init__(message, code="AUTHORIZATION_ERROR", details=details, **kwargs)


class ServiceException(PlatformException):
    """Exception raised for service errors."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        retryable: bool = False,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if service_name:
            details["service"] = service_name
        details["retryable"] = retryable
        super().__init__(message, code="SERVICE_ERROR", details=details, **kwargs)
        self.service_name = service_name
        self.retryable = retryable


class ToolExecutionException(PlatformException):
    """Exception raised for external tool execution errors."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if tool_name:
            details["tool"] = tool_name
        if exit_code is not None:
            details["exit_code"] = exit_code
        if stdout:
            details["stdout"] = stdout
        if stderr:
            details["stderr"] = stderr
        super().__init__(message, code="TOOL_EXECUTION_ERROR", details=details, **kwargs)
        self.tool_name = tool_name
        self.exit_code = exit_code


def handle_exception(
    exception: Exception,
    logger: Optional[structlog.BoundLogger] = None,
    reraise: bool = True,
) -> dict:
    """Handle an exception and return a dictionary representation.

    Args:
        exception: The exception to handle
        logger: Optional logger to log the exception
        reraise: Whether to re-raise the exception after handling

    Returns:
        Dictionary representation of the exception
    """
    if logger:
        logger.error(
            "Exception occurred",
            error=type(exception).__name__,
            message=str(exception),
            exc_info=True,
        )

    if isinstance(exception, PlatformException):
        result = exception.to_dict()
    else:
        result = {
            "error": type(exception).__name__,
            "message": str(exception),
            "code": "UNKNOWN_ERROR",
            "details": {},
        }

    if reraise:
        raise exception

    return result
