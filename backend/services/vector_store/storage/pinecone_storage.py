"""Pinecone vector storage implementation."""

import logging
from typing import List, Dict, Any

from ..interfaces.vector_store import VectorStorageInterface
from ..exceptions.vector_store_exceptions import VectorStorageError

logger = logging.getLogger(__name__)

class PineconeVectorStorage(VectorStorageInterface):
    """Implementation of vector storage operations for Pinecone."""
    
    def __init__(self, pinecone_index):
        """Initialize with a Pinecone index."""
        self.index = pinecone_index
    
    async def upsert_vectors(
        self,
        repository_id: int,
        vectors: List[Dict[str, Any]],
        namespace: str
    ) -> None:
        """Upload vectors to Pinecone."""
        try:
            logger.info(f"Starting vector upsert for repository {repository_id} in namespace {namespace}")
            logger.info(f"Total vectors to upsert: {len(vectors)}")
            
            # Format vectors for Pinecone
            pinecone_vectors = []
            for idx, vec in enumerate(vectors):
                pinecone_vectors.append({
                    "id": vec["id"],
                    "values": vec["embedding"],
                    "metadata": vec["metadata"]
                })

            # Log sample vector for debugging
            if pinecone_vectors:
                sample_vec = pinecone_vectors[0]
                logger.info(f"Sample vector metadata: {sample_vec['metadata']}")
                logger.info(f"Sample vector ID: {sample_vec['id']}")
                logger.info(f"Vector dimension: {len(sample_vec['values'])}")
            
            # Upsert in batches of 100
            batch_size = 100
            total_batches = (len(pinecone_vectors) + batch_size - 1) // batch_size
            vectors_upserted = 0
            
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                logger.info(f"Upserting batch {batch_num}/{total_batches} ({len(batch)} vectors)")
                logger.info(f"Namespace being used: {namespace}")
                
                self.index.upsert(vectors=batch, namespace=namespace)
                vectors_upserted += len(batch)
                
            logger.info(f"Successfully upserted {vectors_upserted} vectors to namespace {namespace}")

        except Exception as e:
            logger.error(f"Failed to upsert vectors: {str(e)}")
            raise VectorStorageError(f"Failed to upsert vectors: {str(e)}")
    
    async def delete_repository(self, repository_id: int, namespace: str) -> None:
        """Delete all vectors for a repository."""
        try:
            logger.info(f"Deleting vectors for repository {repository_id} in namespace {namespace}")
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Successfully deleted all vectors in namespace {namespace}")
        except Exception as e:
            logger.error(f"Failed to delete repository vectors: {str(e)}")
            raise VectorStorageError(f"Failed to delete repository vectors: {str(e)}") 