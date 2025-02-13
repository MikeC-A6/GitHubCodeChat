"""Main vector store service combining storage and retrieval operations."""

import logging
from typing import List, Dict, Any, Optional

from .config import PineconeConfig
from .storage.pinecone_storage import PineconeVectorStorage
from .retrieval.pinecone_retrieval import PineconeVectorRetrieval
from .exceptions.vector_store_exceptions import VectorStoreError, VectorStoreConnectionError

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service combining vector storage and retrieval operations."""
    
    def __init__(self):
        """Initialize vector store service with storage and retrieval capabilities."""
        try:
            # Initialize configuration
            self.config = PineconeConfig()
            
            # Initialize Pinecone client and ensure index exists
            self.client = self.config.initialize_client()
            self.config.ensure_index_exists(self.client)
            
            # Get index
            index = self.config.get_index(self.client)
            
            # Initialize storage and retrieval services
            self.storage = PineconeVectorStorage(index)
            self.retrieval = PineconeVectorRetrieval(index, self.config)
            
            logger.info("VectorStoreService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStoreService: {str(e)}")
            raise VectorStoreConnectionError(str(e))
    
    def set_retrieval_config(self, top_k: Optional[int] = None, similarity_metric: Optional[str] = None) -> None:
        """Update retrieval configuration."""
        self.config.set_retrieval_config(top_k=top_k, similarity_metric=similarity_metric)
        logger.info(f"Updated retrieval config: top_k={self.config.retrieval.top_k}, similarity_metric={self.config.retrieval.similarity_metric}")
    
    async def upsert_vectors(
        self,
        repository_id: int,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> None:
        """Upload vectors to the vector store."""
        await self.storage.upsert_vectors(repository_id, vectors, namespace)
    
    async def delete_repository(
        self,
        repository_id: int,
        namespace: Optional[str] = None
    ) -> None:
        """Delete all vectors for a repository."""
        await self.storage.delete_repository(repository_id, namespace)
    
    async def query_similar(
        self,
        query_embedding: List[float],
        repository_id: Optional[int] = None,
        namespace: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query similar vectors."""
        return await self.retrieval.query_similar(
            query_embedding=query_embedding,
            repository_id=repository_id,
            namespace=namespace,
            top_k=top_k
        ) 