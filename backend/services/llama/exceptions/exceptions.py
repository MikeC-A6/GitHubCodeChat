"""Custom exceptions for the LlamaIndex service."""

class LlamaServiceError(Exception):
    """Base exception for LlamaService"""
    pass

class DocumentLoadError(LlamaServiceError):
    """Raised when there's an error loading documents"""
    pass

class VectorStoreError(LlamaServiceError):
    """Raised when there's an error with vector store operations"""
    pass

class ChatError(LlamaServiceError):
    """Raised when there's an error in chat processing"""
    pass

class ConfigurationError(LlamaServiceError):
    """Raised when there's an error with service configuration"""
    pass

class RetryableError(Exception):
    """Raised when an operation fails but can be retried."""
    pass

def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, TooManyRequests

    retryable_exceptions = (
        ResourceExhausted,  # 429 errors
        ServiceUnavailable,  # 503 errors
        TooManyRequests,    # Another form of 429
        RetryableError
    )
    
    return isinstance(error, retryable_exceptions) 