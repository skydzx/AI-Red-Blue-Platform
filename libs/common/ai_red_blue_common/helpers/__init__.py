"""Helper utilities for AI Red Blue Platform."""

import hashlib
import json
import random
import string
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")


def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short alphanumeric ID.

    Args:
        length: Length of the ID (default: 8)

    Returns:
        Random alphanumeric string
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def hash_data(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """Hash data using specified algorithm.

    Args:
        data: Data to hash (string or bytes)
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hexadecimal hash string
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary to merge into base

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing unsafe characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove unsafe characters
    unsafe_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    result = "".join(c if c not in unsafe_chars else "_" for c in filename)
    # Remove leading/trailing whitespace and dots
    result = result.strip(" .")
    # Limit length
    return result[:255] if result else "unnamed"


def format_timestamp(
    dt: datetime,
    timezone: Optional[timezone] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a datetime object to string.

    Args:
        dt: Datetime object
        timezone: Optional timezone to convert to
        format_str: Format string

    Returns:
        Formatted timestamp string
    """
    if timezone:
        dt = dt.astimezone(timezone)
    return dt.strftime(format_str)


def parse_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse a timestamp string to datetime.

    Args:
        timestamp: Timestamp string
        format_str: Format string

    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp, format_str)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for retrying a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    # Wait before retrying
                    import time

                    time.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper

    return decorator


class Singleton(type):
    """Metaclass for creating singleton classes."""

    _instances: dict = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def class_to_dict(obj: Any) -> dict:
    """Convert an object to dictionary, handling nested objects.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation
    """
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: class_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [class_to_dict(item) for item in obj]
    if hasattr(obj, "__dict__"):
        return class_to_dict(obj.__dict__)
    return str(obj)


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON data, returning default on failure.

    Args:
        data: JSON string to parse
        default: Default value on parse failure

    Returns:
        Parsed JSON or default
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def chunk_list(lst: list[T], size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        size: Chunk size

    Returns:
        List of chunks
    """
    return [lst[i : i + size] for i in range(0, len(lst), size)]
