"""Exceptions for vector store operations."""

class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass

class VectorStorageError(VectorStoreError):
    """Exception raised for errors during vector storage operations."""
    pass

class VectorRetrievalError(VectorStoreError):
    """Exception raised for errors during vector retrieval operations."""
    pass

class VectorStoreConnectionError(VectorStoreError):
    """Exception raised for errors during vector store connection."""
    pass 