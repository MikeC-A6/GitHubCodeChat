"""Configuration management for LlamaIndex service."""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from llama_index.llms.gemini import Gemini
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from pinecone import Pinecone, ServerlessSpec

from ..exceptions.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

@dataclass
class RetrievalConfig:
    """Configuration for document retrieval."""
    similarity_top_k: int = 20
    chat_mode: str = "condense_plus_context"
    verbose: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for chat engine."""
        return {
            "chat_mode": self.chat_mode,
            "verbose": self.verbose,
            "similarity_top_k": self.similarity_top_k
        }

class LlamaConfig:
    """Configuration manager for LlamaIndex service."""
    
    def __init__(self):
        self.pinecone_client: Optional[Pinecone] = None
        self.llm: Optional[Gemini] = None
        self.embed_model: Optional[OpenAIEmbedding] = None
        self.index_name: str = "codebases"
        self.retrieval_config = RetrievalConfig()
        
    def set_retrieval_config(
        self,
        similarity_top_k: Optional[int] = None,
        chat_mode: Optional[str] = None,
        verbose: Optional[bool] = None
    ) -> None:
        """Update retrieval configuration parameters."""
        if similarity_top_k is not None:
            if similarity_top_k <= 0:
                raise ConfigurationError("similarity_top_k must be greater than 0")
            if similarity_top_k > 50:  # Prevent retrieving too many documents
                raise ConfigurationError("similarity_top_k cannot exceed 50 to prevent performance issues")
            self.retrieval_config.similarity_top_k = similarity_top_k
            
        if chat_mode is not None:
            self.retrieval_config.chat_mode = chat_mode
            
        if verbose is not None:
            self.retrieval_config.verbose = verbose
        
        logger.info(f"Updated retrieval config: {self.retrieval_config}")
        
    def get_retrieval_config(self) -> Dict[str, Any]:
        """Get the current retrieval configuration."""
        return self.retrieval_config.to_dict()
        
    def initialize(self) -> None:
        """Initialize all configurations and clients."""
        try:
            # Get API keys
            pinecone_api_key = os.environ.get('PINECONE_API_KEY') or os.environ.get('REPLIT_PINECONE_API_KEY')
            openai_api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('REPLIT_OPENAI_API_KEY')
            gemini_api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('REPLIT_GEMINI_API_KEY')
            
            # Validate API keys
            if not all([pinecone_api_key, openai_api_key, gemini_api_key]):
                missing_keys = []
                if not pinecone_api_key: missing_keys.append("PINECONE_API_KEY")
                if not openai_api_key: missing_keys.append("OPENAI_API_KEY")
                if not gemini_api_key: missing_keys.append("GEMINI_API_KEY")
                raise ConfigurationError(f"Missing required API keys: {', '.join(missing_keys)}")
            
            # Initialize Pinecone
            self.pinecone_client = Pinecone(api_key=pinecone_api_key)
            
            # Initialize Gemini
            self.llm = Gemini(
                api_key=gemini_api_key,
                model="models/gemini-2.0-flash",
                temperature=0.1,
                max_tokens=4096
            )
            
            # Initialize embedding model
            self.embed_model = OpenAIEmbedding(
                api_key=openai_api_key,
                model_name="text-embedding-3-large",
                dimensions=3072
            )
            
            # Configure global settings
            Settings.llm = self.llm
            Settings.embed_model = self.embed_model
            
            logger.info("LlamaConfig initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaConfig: {str(e)}")
            raise ConfigurationError(f"Configuration initialization failed: {str(e)}")
    
    def ensure_index_exists(self) -> None:
        """Ensure Pinecone index exists, create if it doesn't."""
        if not self.pinecone_client:
            raise ConfigurationError("Pinecone client not initialized")
            
        if self.index_name not in self.pinecone_client.list_indexes().names():
            self.pinecone_client.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info(f"Created new Pinecone index: {self.index_name}")
        
    def get_pinecone_index(self):
        """Get the Pinecone index instance."""
        if not self.pinecone_client:
            raise ConfigurationError("Pinecone client not initialized")
        return self.pinecone_client.Index(self.index_name) 