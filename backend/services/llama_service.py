# Standard library imports
import os
from typing import List, Dict, Any
from pathlib import Path

# LlamaIndex core imports
from llama_index import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
)

# LlamaIndex components
from llama_index.llms.gemini import Gemini
from llama_index.embeddings import OpenAIEmbedding
from llama_index.node_parser import SimpleNodeParser
from llama_index.vector_stores.postgres import PGVectorStore

# Custom exceptions
class LlamaServiceError(Exception):
    """Base exception for LlamaService"""
    pass

class DocumentLoadError(LlamaServiceError):
    """Raised when there's an error loading documents"""
    pass

class DatabaseConnectionError(LlamaServiceError):
    """Raised when there's an error connecting to the database"""
    pass

class ChatError(LlamaServiceError):
    """Raised when there's an error in chat processing"""
    pass

class LlamaService:
    def __init__(self):
        try:
            # Validate environment variables
            self._validate_environment()
            
            # Configure global settings with Gemini LLM
            self._configure_settings()
            
            # Initialize storage
            self.documents = None
            self.index = None
            
            # Initialize vector store
            self._initialize_vector_store()
            
            # Load documents
            self._initialize_documents()
            
        except Exception as e:
            raise LlamaServiceError(f"Failed to initialize LlamaService: {str(e)}")

    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "DATABASE_URL": os.getenv("DATABASE_URL")
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise LlamaServiceError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def _configure_settings(self):
        """Configure LlamaIndex settings"""
        try:
            Settings.llm = Gemini(
                api_key=os.getenv("GEMINI_API_KEY"),
                model_name="models/gemini-pro"
            )
            Settings.embed_model = OpenAIEmbedding(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name="text-embedding-3-large"
            )
            Settings.node_parser = SimpleNodeParser.from_defaults()
        except Exception as e:
            raise LlamaServiceError(f"Failed to configure settings: {str(e)}")

    def _initialize_vector_store(self):
        """Initialize the vector store connection"""
        try:
            db_url = os.getenv("DATABASE_URL")
            async_db_url = db_url.replace('postgres://', 'postgresql+asyncpg://')
            
            self.vector_store = PGVectorStore(
                connection_string=db_url,
                async_connection_string=async_db_url,
                schema_name="public",
                table_name="embeddings",
                embed_dim=3072
            )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize vector store: {str(e)}")

    def _initialize_documents(self):
        """Initialize and load documents"""
        try:
            data_dir = Path("./data")
            if not data_dir.exists():
                raise DocumentLoadError("Data directory does not exist")
                
            self.documents = SimpleDirectoryReader(
                input_dir=str(data_dir)
            ).load_data()
            
            if not self.documents:
                raise DocumentLoadError("No documents found in data directory")
                
            self.index = VectorStoreIndex.from_documents(
                self.documents,
            )
        except DocumentLoadError as e:
            print(f"Warning: {str(e)}")
            self.documents = []
            self.index = None
        except Exception as e:
            raise DocumentLoadError(f"Failed to load documents: {str(e)}")

    async def chat(
        self, 
        repository_id: int, 
        message: str, 
        chat_history: List[Dict[str, str]]
    ) -> str:
        """Generate response using Gemini model with context from pgvector"""
        try:
            if not message.strip():
                raise ChatError("Empty message provided")

            if not self.vector_store:
                raise ChatError("Vector store not initialized")

            # Create index from vector store
            index = await VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )

            # Create chat engine
            chat_engine = index.as_chat_engine(
                chat_mode="condense_plus_context",
                verbose=True,
                similarity_top_k=5
            )

            # Format chat history
            formatted_history = [
                (msg["role"], msg["content"]) 
                for msg in chat_history
                if msg.get("role") and msg.get("content")
            ]

            # Generate response
            response = await chat_engine.achat(
                message=message,
                chat_history=formatted_history
            )

            if not response or not response.response:
                raise ChatError("Failed to generate response")

            return response.response

        except ChatError as e:
            raise e
        except Exception as e:
            raise ChatError(f"Error in chat service: {str(e)}")