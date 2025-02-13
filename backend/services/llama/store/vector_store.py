"""Vector store management for LlamaIndex service."""

import logging
from typing import List

from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

from ..exceptions import VectorStoreError
from ...vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manager for vector store operations."""
    
    def __init__(self, pinecone_index):
        """Initialize vector store manager with a Pinecone index."""
        # Log initial index stats
        stats = pinecone_index.describe_index_stats()
        logger.info(f"Initial index stats: {stats}")
        
        # Initialize LlamaIndex vector store
        self.vector_store = PineconeVectorStore(
            pinecone_index=pinecone_index,
            namespace="repo_githubcloner",  # Set namespace for all operations
            text_key="chunk_content",  # Match the actual field name in Pinecone
            metadata_key="metadata"  # Key for additional metadata
        )
        
        # Initialize our vector store service for additional operations
        self.vector_store_service = VectorStoreService()
        
    def create_repository_filter(self, repository_ids: List[int]) -> MetadataFilters:
        """Create a metadata filter for repository IDs."""
        try:
            repo_id_strs = [str(repo_id) for repo_id in repository_ids]
            logger.info(f"Creating filter for repository IDs: {repo_id_strs}")
            
            filters = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="repository_id",
                        operator=FilterOperator.IN,
                        value=repo_id_strs
                    )
                ]
            )
            logger.info(f"Created metadata filters: {filters}")
            return filters
            
        except Exception as e:
            logger.error(f"Failed to create repository filter: {str(e)}")
            raise VectorStoreError(f"Failed to create repository filter: {str(e)}")
    
    def get_vector_store(self) -> PineconeVectorStore:
        """Get the vector store instance."""
        return self.vector_store 