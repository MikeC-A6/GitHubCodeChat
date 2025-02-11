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