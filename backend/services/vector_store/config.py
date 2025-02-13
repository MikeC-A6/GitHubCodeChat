"""Configuration for vector store services."""

import os
from dataclasses import dataclass
from pinecone import Pinecone, ServerlessSpec
from .exceptions.vector_store_exceptions import VectorStoreConnectionError

@dataclass
class RetrievalConfig:
    """Configuration for vector retrieval."""
    top_k: int = 5
    similarity_metric: str = "cosine"

class PineconeConfig:
    """Configuration for Pinecone vector store."""
    
    def __init__(self):
        """Initialize Pinecone configuration."""
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.index_name = "projectcode"
        self.dimension = 1536  # text-embedding-3-small dimensions
        self.host = "https://projectcode-6xdvrp1.svc.aped-4627-b74a.pinecone.io"
        
        # Initialize retrieval configuration
        self.retrieval = RetrievalConfig()
        
    def set_retrieval_config(
        self,
        top_k: int = None,
        similarity_metric: str = None
    ) -> None:
        """Update retrieval configuration."""
        if top_k is not None:
            if top_k <= 0:
                raise ValueError("top_k must be greater than 0")
            if top_k > 100:  # Prevent retrieving too many results
                raise ValueError("top_k cannot exceed 100 to prevent performance issues")
            self.retrieval.top_k = top_k
            
        if similarity_metric is not None:
            if similarity_metric not in ["cosine", "euclidean", "dot"]:
                raise ValueError("similarity_metric must be one of: cosine, euclidean, dot")
            self.retrieval.similarity_metric = similarity_metric
        
    def initialize_client(self) -> Pinecone:
        """Initialize and return Pinecone client."""
        try:
            return Pinecone(api_key=self.api_key)
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to initialize Pinecone client: {str(e)}")
    
    def ensure_index_exists(self, client: Pinecone) -> None:
        """Ensure the required index exists, create if it doesn't."""
        try:
            try:
                client.Index(self.index_name, host=self.host)
            except Exception:
                # Index doesn't exist, create it
                client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to ensure index exists: {str(e)}")
    
    def get_index(self, client: Pinecone):
        """Get the Pinecone index."""
        try:
            return client.Index(self.index_name, host=self.host)
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to get index: {str(e)}") 