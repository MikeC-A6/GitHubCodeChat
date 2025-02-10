# Standard library imports
import os
from typing import List, Dict, Any
from pathlib import Path
import logging

# LlamaIndex core imports
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext
)

# LlamaIndex components
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import pinecone

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
        # Initialize Pinecone
        pinecone.init(
            api_key=os.environ.get('PINECONE_API_KEY') or environ.get('REPLIT_PINECONE_API_KEY'),
            environment="gcp-starter"  # Using the default starter environment
        )
        self.index_name = "codebases"  # Using our existing index name
        
        # Initialize Gemini
        self.llm = Gemini(
            api_key=os.environ.get('GEMINI_API_KEY') or environ.get('REPLIT_GEMINI_API_KEY'),
            model="gemini-2.0-flash",
            temperature=0.1,
            max_tokens=4096
        )
        
        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(
            api_key=os.environ.get('OPENAI_API_KEY') or environ.get('REPLIT_OPENAI_API_KEY'),
            model_name="text-embedding-3-small"
        )
        
        # Set up LlamaIndex
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            pinecone_index=pinecone.Index(self.index_name)
        )

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
            # Create metadata filter for the specified repositories
            metadata_filters = {"repository_id": {"$in": repository_ids}}
            
            # Create vector store index with the filter
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                service_context=ServiceContext.from_defaults(
                    llm=self.llm,
                    embed_model=self.embed_model
                )
            )
            
            # Create chat engine
            chat_engine = index.as_chat_engine(
                chat_mode="condense_plus_context",
                verbose=True,
                metadata_filters=metadata_filters,
                similarity_top_k=5
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
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise Exception(f"Failed to process chat message: {str(e)}")