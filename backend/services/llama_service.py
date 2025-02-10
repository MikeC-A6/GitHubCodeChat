# Standard library imports
import os
from typing import List, Dict, Any
from pathlib import Path
import logging

# LlamaIndex core imports
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader
)

# LlamaIndex components
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.node_parser import NodeParser
from pinecone import Pinecone, ServerlessSpec
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

# Custom exceptions
class LlamaServiceError(Exception):
    """Base exception for LlamaService"""
    pass

class DocumentLoadError(LlamaServiceError):
    """Raised when there's an error loading documents"""
    pass

class VectorStoreError(LlamaServiceError):
    """Raised when there's an error with vector store operations"""
    pass

class ChatError(LlamaServiceError):
    """Raised when there's an error in chat processing"""
    pass

logger = logging.getLogger(__name__)

class LlamaService:
    def __init__(self):
        """Initialize LlamaIndex with Gemini and Pinecone"""
        try:
            # Get API keys from environment variables or Replit secrets
            pinecone_api_key = os.environ.get('PINECONE_API_KEY') or environ.get('REPLIT_PINECONE_API_KEY')
            openai_api_key = os.environ.get('OPENAI_API_KEY') or environ.get('REPLIT_OPENAI_API_KEY')
            gemini_api_key = os.environ.get('GEMINI_API_KEY') or environ.get('REPLIT_GEMINI_API_KEY')
            
            # Validate required environment variables
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            # Initialize Pinecone with new syntax
            pc = Pinecone(api_key=pinecone_api_key)
            self.index_name = "codebases"
            
            # Create index if it doesn't exist
            if self.index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=self.index_name,
                    dimension=3072,  # text-embedding-3-small dimensions
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
            
            # Get the index
            pinecone_index = pc.Index(self.index_name)
            
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
            
            # Set up LlamaIndex
            Settings.llm = self.llm
            Settings.embed_model = self.embed_model
            
            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index,
                metadata_filters={"repository_id": {"$in": []}},  # Default empty filter
                text_key="chunk_content",  # The field containing the text content
                metadata_key="metadata"  # The field containing metadata
            )
            
            logger.info("LlamaService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LlamaService: {str(e)}")
            raise

    async def chat(
        self,
        repository_ids: List[int],
        message: str,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Process a chat message using LlamaIndex and Gemini
        """
        try:
            # Convert repository IDs to strings
            repo_id_strs = [str(repo_id) for repo_id in repository_ids]
            
            # Create metadata filter for repository IDs
            metadata_filter = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="repository_id",
                        operator=FilterOperator.IN,
                        value=repo_id_strs
                    )
                ]
            )
            
            # Create vector store index
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )
            
            # Create chat engine with metadata filters
            chat_engine = index.as_chat_engine(
                chat_mode="condense_plus_context",
                verbose=True,
                similarity_top_k=5,
                filters=metadata_filter
            )
            
            # Convert chat history to the format expected by LlamaIndex
            formatted_history = []
            for msg in chat_history:
                formatted_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Get response
            response = await chat_engine.achat(
                message=message,
                chat_history=formatted_history
            )
            
            # Handle response properly
            if hasattr(response, 'response'):
                return str(response.response)
            elif hasattr(response, 'message'):
                return str(response.message)
            else:
                return str(response)
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            if hasattr(e, 'response'):
                logger.error(f"Response error details: {e.response}")
            raise ChatError(f"Failed to process chat message: {str(e)}")