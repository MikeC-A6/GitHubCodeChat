"""Pinecone vector retrieval implementation."""

import logging
from typing import List, Dict, Any, Optional

from ..interfaces.vector_store import VectorRetrievalInterface
from ..exceptions.vector_store_exceptions import VectorRetrievalError
from ..config import PineconeConfig

logger = logging.getLogger(__name__)

class PineconeVectorRetrieval(VectorRetrievalInterface):
    """Implementation of vector retrieval operations for Pinecone."""
    
    def __init__(self, pinecone_index, config: PineconeConfig):
        """Initialize with a Pinecone index and config."""
        self.index = pinecone_index
        self.config = config
    
    async def query_similar(
        self,
        query_embedding: List[float],
        repository_id: Optional[int] = None,
        namespace: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query similar vectors from Pinecone."""
        try:
            logger.info(f"Querying vectors for repository_id={repository_id}, namespace={namespace}")
            logger.info(f"Query vector dimension: {len(query_embedding)}")
            
            # Use provided top_k or fall back to config value
            effective_top_k = top_k if top_k is not None else self.config.retrieval.top_k
            logger.info(f"Using top_k={effective_top_k}")
            
            # Build filter
            filter_dict = {}
            if repository_id is not None:
                filter_dict["repository_id"] = str(repository_id)
            logger.info(f"Applying filter: {filter_dict}")
            
            # Log index stats before query
            stats = self.index.describe_index_stats()
            logger.info(f"Total vectors in index: {stats.total_vector_count}")
            if namespace:
                namespace_stats = stats.namespaces.get(namespace, {})
                logger.info(f"Vectors in namespace {namespace}: {namespace_stats.get('vector_count', 0)}")

            # Execute query
            response = self.index.query(
                vector=query_embedding,
                top_k=effective_top_k,
                include_metadata=True,
                filter=filter_dict,
                namespace=namespace
            )
            
            # Log query results
            logger.info(f"Number of matches returned: {len(response.matches)}")
            if response.matches:
                logger.info(f"Top match score: {response.matches[0].score}")
                logger.info(f"Top match metadata: {response.matches[0].metadata}")

            # Format response
            return [{
                "score": match.score,
                "repository_id": int(match.metadata["repository_id"]),
                "file_name": match.metadata["file_name"],
                "content": match.metadata["content"]
            } for match in response.matches]

        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise VectorRetrievalError(f"Failed to query vectors: {str(e)}") 