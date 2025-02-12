"""Retry utilities for async operations."""

import asyncio
import logging
from functools import wraps
from typing import TypeVar, Callable, Any
from ..exceptions.exceptions import is_retryable_error

logger = logging.getLogger(__name__)

T = TypeVar('T')

def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0
):
    """
    Decorator for async functions to implement exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retries before giving up
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_error(e) or attempt == max_retries:
                        raise last_exception
                    
                    # Calculate next delay with exponential backoff
                    wait_time = min(delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed with error: {str(e)}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception  # Should never reach here, but just in case
            
        return wrapper
    return decorator 