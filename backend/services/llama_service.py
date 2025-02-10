from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.openai import OpenAIEmbedding
import os
from typing import List, Dict, Any

class LlamaService:
    def __init__(self):
        # Initialize Gemini LLM
        self.llm = Gemini(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name="gemini-2.0-flash"
        )

        # Initialize OpenAI embeddings
        self.embed_model = OpenAIEmbedding(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-large"
        )

        # Initialize pgvector store
        self.vector_store = PGVectorStore(
            connection_string=os.getenv("DATABASE_URL"),
            table_name="embeddings",
            embed_dim=3072  # dimension for text-embedding-3-large
        )

        # Initialize service context
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model=self.embed_model
        )

    async def chat(
        self, 
        repository_id: int, 
        message: str, 
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate response using Gemini model with context from pgvector
        """
        try:
            # Create index from vector store
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                service_context=self.service_context
            )

            # Create chat engine with similarity search
            chat_engine = index.as_chat_engine(
                chat_mode="condense_plus_context",
                verbose=True,
                similarity_top_k=5  # number of relevant chunks to retrieve
            )

            # Format chat history
            formatted_history = [
                (msg["role"], msg["content"]) 
                for msg in chat_history
            ]

            # Generate response
            response = await chat_engine.achat(
                message=message,
                chat_history=formatted_history
            )

            return response.response

        except Exception as e:
            print(f"Error in chat service: {str(e)}")
            raise