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

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manager for vector store operations."""
    
    def __init__(self, pinecone_index):
        """Initialize vector store manager with a Pinecone index."""
        self.vector_store = PineconeVectorStore(
            pinecone_index=pinecone_index,
            metadata_filters={"repository_id": {"$in": []}},
            text_key="chunk_content",
            metadata_key="metadata"
        )
        
    def create_repository_filter(self, repository_ids: List[int]) -> MetadataFilters:
        """Create a metadata filter for repository IDs."""
        try:
            repo_id_strs = [str(repo_id) for repo_id in repository_ids]
            return MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="repository_id",
                        operator=FilterOperator.IN,
                        value=repo_id_strs
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Failed to create repository filter: {str(e)}")
            raise VectorStoreError(f"Failed to create repository filter: {str(e)}")
    
    def get_vector_store(self) -> PineconeVectorStore:
        """Get the vector store instance."""
        return self.vector_store 