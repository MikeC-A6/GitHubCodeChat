# Standard library imports
import os
from typing import List, Dict, Any
from pathlib import Path

# LlamaIndex core imports
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
)

# LlamaIndex components
from llama_index.llms.gemini import Gemini
from llama_index.embeddings import OpenAIEmbedding
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
            "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY")
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
        """Initialize the Pinecone vector store"""
        try:
            # Initialize Pinecone client
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

            # Index name for our application
            index_name = "repo-analysis"

            # Create index if it doesn't exist
            if index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=index_name,
                    dimension=3072,  # Using OpenAI text-embedding-3-large dimensions
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )

            # Get the index
            pinecone_index = pc.Index(index_name)

            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                pinecone_index=pinecone_index
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Pinecone vector store: {str(e)}")

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
                vector_store=self.vector_store
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
        """Generate response using Gemini model with context from Pinecone"""
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