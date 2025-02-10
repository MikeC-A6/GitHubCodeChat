from llama_index import VectorStoreIndex, ServiceContext
from llama_index.vector_stores import PGVectorStore
from llama_index.llms import Gemini
import os

class LlamaService:
    def __init__(self):
        self.llm = Gemini(
            api_key=os.getenv("GEMINI_API_KEY"),
            model_name="gemini-2.0-flash"
        )
        
        self.vector_store = PGVectorStore(
            connection_string=os.getenv("DATABASE_URL"),
            table_name="embeddings"
        )
        
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model="local:BAAI/bge-small-en-v1.5"
        )

    async def chat(self, repository_id: int, message: str, chat_history: list[dict]):
        # Retrieve the index for this repository
        index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            service_context=self.service_context
        )
        
        # Create chat engine
        chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            verbose=True
        )
        
        # Get response
        response = await chat_engine.chat(
            message,
            chat_history=[
                (msg["role"], msg["content"]) for msg in chat_history
            ]
        )
        
        return response.response
