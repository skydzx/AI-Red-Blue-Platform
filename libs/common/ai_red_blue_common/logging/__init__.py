"""Logging configuration for AI Red Blue Platform."""

import logging
import sys
from contextlib import contextmanager
from functools import lru_cache
from typing import Optional

import structlog


@lru_cache()
def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    structured: bool = True,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        structured: Whether to use structured logging
    """
    from ai_red_blue_common import get_settings

    settings = get_settings()
    level = log_level or settings.log_level.upper()
    fmt = log_format or settings.log_format

    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format=fmt if not structured else None,
        stream=sys.stdout,
    )

    if structured:
        # Configure structlog for structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer() if settings.is_production else None,
                structlog.processors.JSONRenderer() if settings.is_production else None,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Simple format-based logging
        logging.basicConfig(format=fmt)


def get_logger(
    name: str,
    module: Optional[str] = None,
    bind: Optional[dict] = None,
) -> structlog.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)
        module: Optional module name to append to logger
        bind: Optional dictionary of values to bind to logger

    Returns:
        Configured logger instance
    """
    module_name = f"{module}.{name}" if module else name
    logger = structlog.get_logger(module_name)

    if bind:
        logger = logger.bind(**bind)

    return logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this instance."""
        return get_logger(self.__class__.__name__.lower())


@contextmanager
def log_execution(logger: structlog.BoundLogger, action: str = "executing"):
    """Context manager to log function execution.

    Args:
        logger: Logger instance
        action: Action description (e.g., "executing", "processing")
    """
    logger.info(f"Started {action}")
    try:
        yield
        logger.info(f"Finished {action}")
    except Exception as e:
        logger.error(f"Failed {action}", error=str(e), exc_info=True)
        raise
