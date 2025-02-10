from pinecone import Pinecone, ServerlessSpec
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class VectorStoreError(Exception):
    """Base exception for vector store operations"""
    pass

class VectorStoreService:
    def __init__(self):
        """
        Initialize Pinecone client and ensure index exists
        Using text-embedding-3-large which has 3072 dimensions
        """
        try:
            pinecone_api_key = os.environ.get("PINECONE_API_KEY")
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables")

            self.pc = Pinecone(api_key=pinecone_api_key)
            self.index_name = "codebases"
            self.dimension = 3072  # text-embedding-3-large dimensions

            # Get or create index using ServerlessSpec
            try:
                self.index = self.pc.Index(self.index_name)
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
                self.index = self.pc.Index(self.index_name)

        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Pinecone: {str(e)}")

    async def upsert_vectors(
        self,
        repository_id: int,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """
        Upload vectors to Pinecone

        Args:
            repository_id: ID of the repository in PostgreSQL
            vectors: List of vectors from the embeddings service
                    Each vector should have: file_name, embedding, content, metadata
        """
        try:
            # Format vectors for Pinecone
            pinecone_vectors = []
            for idx, vec in enumerate(vectors):
                vector_id = f"repo_{repository_id}_file_{idx}"
                pinecone_vectors.append({
                    "id": vector_id,
                    "values": vec["embedding"],
                    "metadata": {
                        **vec["metadata"],
                        "repository_id": str(repository_id),
                        "file_path": vec["file_name"],
                        "chunk_content": vec["content"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)

        except Exception as e:
            raise VectorStoreError(f"Failed to upsert vectors: {str(e)}")

    async def delete_repository(self, repository_id: int) -> None:
        """Delete all vectors for a repository"""
        try:
            # Delete vectors by metadata filter
            self.index.delete(
                filter={"repository_id": str(repository_id)}
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to delete repository vectors: {str(e)}")

    async def query_similar(
        self,
        query_embedding: List[float],
        repository_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors

        Args:
            query_embedding: The query vector
            repository_id: Optional repository ID to filter results
            top_k: Number of results to return
        """
        try:
            filter_dict = {}
            if repository_id is not None:
                filter_dict["repository_id"] = str(repository_id)

            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

            return [{
                "score": match.score,
                "repository_id": int(match.metadata["repository_id"]),
                "file_name": match.metadata["file_name"],
                "content": match.metadata["chunk_content"]
            } for match in response.matches]

        except Exception as e:
            raise VectorStoreError(f"Failed to query vectors: {str(e)}")