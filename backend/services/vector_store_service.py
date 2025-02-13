from pinecone import Pinecone, ServerlessSpec
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VectorStoreError(Exception):
    """Base exception for vector store operations"""
    pass

class VectorStoreService:
    def __init__(self):
        """
        Initialize Pinecone client and ensure index exists
        Using text-embedding-3-small which has 1536 dimensions
        """
        try:
            self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
            self.index_name = "projectcode"
            self.dimension = 1536  # text-embedding-3-small dimensions

            # Get or create index
            try:
                self.index = self.pc.Index(
                    self.index_name,
                    host="https://projectcode-6xdvrp1.svc.aped-4627-b74a.pinecone.io"
                )
            except Exception:
                # Index doesn't exist, create it
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                self.index = self.pc.Index(
                    self.index_name,
                    host="https://projectcode-6xdvrp1.svc.aped-4627-b74a.pinecone.io"
                )

        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Pinecone: {str(e)}")

    async def upsert_vectors(
        self,
        repository_id: int,
        vectors: List[Dict[str, Any]],
        namespace: str
    ) -> None:
        """
        Upload vectors to Pinecone
        
        Args:
            repository_id: ID of the repository in PostgreSQL
            vectors: List of vectors from the embeddings service
                    Each vector should have: file_name, embedding, content, metadata
            namespace: Pinecone namespace for the repository
        """
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

            # Upsert in batches of 100
            batch_size = 100
            total_batches = (len(pinecone_vectors) + batch_size - 1) // batch_size
            vectors_upserted = 0
            
            # Log sample vector for debugging
            if pinecone_vectors:
                sample_vec = pinecone_vectors[0]
                logger.info(f"Sample vector metadata: {sample_vec['metadata']}")
                logger.info(f"Sample vector ID: {sample_vec['id']}")
                logger.info(f"Vector dimension: {len(sample_vec['values'])}")
            
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
            raise VectorStoreError(f"Failed to upsert vectors: {str(e)}")

    async def delete_repository(self, repository_id: int, namespace: str) -> None:
        """
        Delete all vectors for a repository
        
        Args:
            repository_id: Repository ID to delete vectors for
            namespace: Pinecone namespace for the repository
        """
        try:
            # Delete entire namespace
            self.index.delete(delete_all=True, namespace=namespace)
        except Exception as e:
            raise VectorStoreError(f"Failed to delete repository vectors: {str(e)}")

    async def query_similar(
        self,
        query_embedding: List[float],
        repository_id: Optional[int] = None,
        namespace: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        logger.info(f"Querying vectors for repository_id={repository_id}, namespace={namespace}")
        logger.info(f"Query vector dimension: {len(query_embedding)}")
        """
        Query similar vectors
        
        Args:
            query_embedding: The query vector
            repository_id: Optional repository ID to filter results
            namespace: Optional namespace to restrict search to
            top_k: Number of results to return
        """
        try:
            filter_dict = {}
            if repository_id is not None:
                filter_dict["repository_id"] = str(repository_id)
            
            logger.info(f"Applying filter: {filter_dict}")
            
            # Get total vectors in namespace before query
            stats = self.index.describe_index_stats()
            logger.info(f"Total vectors in index: {stats.total_vector_count}")
            if namespace:
                namespace_stats = stats.namespaces.get(namespace, {})
                logger.info(f"Vectors in namespace {namespace}: {namespace_stats.get('vector_count', 0)}")

            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict,
                namespace=namespace
            )
            
            logger.info(f"Number of matches returned: {len(response.matches)}")
            if response.matches:
                logger.info(f"Top match score: {response.matches[0].score}")
                logger.info(f"Top match metadata: {response.matches[0].metadata}")

            return [{
                "score": match.score,
                "repository_id": int(match.metadata["repository_id"]),
                "file_name": match.metadata["file_name"],
                "content": match.metadata["content"]
            } for match in response.matches]

        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise VectorStoreError(f"Failed to query vectors: {str(e)}") 