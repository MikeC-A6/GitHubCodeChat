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
            # Initialize Pinecone
            pinecone_api_key = os.environ.get('PINECONE_API_KEY') or os.environ.get('REPLIT_PINECONE_API_KEY')
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY not found in environment variables")

            # Create Pinecone instance with new API
            self.pc = Pinecone(api_key=pinecone_api_key)
            self.index_name = "codebases"

            # Get or create index using ServerlessSpec
            try:
                self.index = self.pc.Index(self.index_name)
            except Exception:
                # Index doesn't exist, create it
                self.pc.create_index(
                    name=self.index_name,
                    dimension=3072,  # Using text-embedding-3-small dimensions
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                self.index = self.pc.Index(self.index_name)

            # Initialize Gemini
            gemini_api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('REPLIT_GEMINI_API_KEY')
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            self.llm = Gemini(
                api_key=gemini_api_key,
                model="models/gemini-2.0-flash",  # Using the correct model name format
                temperature=0.1,
                max_tokens=4096
            )

            # Initialize embedding model
            openai_api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('REPLIT_OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            self.embed_model = OpenAIEmbedding(
                api_key=openai_api_key,
                model_name="text-embedding-3-small"
            )

            # Set up LlamaIndex
            Settings.llm = self.llm
            Settings.embed_model = self.embed_model

            # Initialize vector store with new Pinecone instance
            self.vector_store = PineconeVectorStore(
                pinecone_index=self.index
            )

            logger.info("LlamaService initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing LlamaService: {str(e)}")
            raise LlamaServiceError(f"Failed to initialize LlamaService: {str(e)}")

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
            metadata_filters = {"repository_id": {"$in": [str(repo_id) for repo_id in repository_ids]}}

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
            formatted_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in chat_history
            ]

            # Get response
            response = await chat_engine.achat(
                message=message,
                chat_history=formatted_history
            )

            return str(response)

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise ChatError(f"Failed to process chat message: {str(e)}")