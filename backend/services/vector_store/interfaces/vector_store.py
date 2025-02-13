"""Interfaces for vector store operations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStorageInterface(ABC):
    """Interface for vector storage operations."""
    
    @abstractmethod
    async def upsert_vectors(
        self,
        repository_id: int,
        vectors: List[Dict[str, Any]],
        namespace: str
    ) -> None:
        """Upload vectors to the vector store."""
        pass
    
    @abstractmethod
    async def delete_repository(
        self,
        repository_id: int,
        namespace: str
    ) -> None:
        """Delete all vectors for a repository."""
        pass

class VectorRetrievalInterface(ABC):
    """Interface for vector retrieval operations."""
    
    @abstractmethod
    async def query_similar(
        self,
        query_embedding: List[float],
        repository_id: Optional[int] = None,
        namespace: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        pass 