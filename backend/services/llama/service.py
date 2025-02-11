"""Main LlamaIndex service implementation."""

import logging
from typing import List, Dict, Optional

from llama_index.core import VectorStoreIndex
from llama_index.core.llms import ChatMessage, MessageRole

from .config.config import LlamaConfig
from .store.vector_store import VectorStoreManager
from .exceptions.exceptions import ChatError

logger = logging.getLogger(__name__)

class LlamaService:
    """Main service class for LlamaIndex operations."""

    def __init__(self):
        """Initialize the LlamaIndex service."""
        try:
            # Initialize configuration
            self.config = LlamaConfig()
            self.config.initialize()
            self.config.ensure_index_exists()

            # Initialize vector store
            pinecone_index = self.config.get_pinecone_index()
            self.vector_store_manager = VectorStoreManager(pinecone_index)

            logger.info("LlamaService initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LlamaService: {str(e)}")
            raise

    def configure_retrieval(
        self,
        similarity_top_k: Optional[int] = None,
        chat_mode: Optional[str] = None,
        verbose: Optional[bool] = None
    ) -> None:
        """Configure document retrieval parameters."""
        self.config.set_retrieval_config(
            similarity_top_k=similarity_top_k,
            chat_mode=chat_mode,
            verbose=verbose
        )

    def _convert_role(self, role: str) -> MessageRole:
        """Convert role string to MessageRole enum."""
        role_map = {
            "user": MessageRole.USER,
            "assistant": MessageRole.ASSISTANT,
            "system": MessageRole.SYSTEM
        }
        return role_map.get(role.lower(), MessageRole.USER)

    async def chat(
        self,
        repository_ids: List[int],
        message: str,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """Process a chat message using LlamaIndex and Gemini."""
        try:
            logger.info(f"Processing chat request for repositories: {repository_ids}")
            logger.info(f"Message: {message}")
            logger.info(f"Chat history length: {len(chat_history)}")

            # Create metadata filter for repository IDs
            metadata_filter = self.vector_store_manager.create_repository_filter(repository_ids)
            logger.info(f"Created metadata filter: {metadata_filter}")

            # Create vector store index
            vector_store = self.vector_store_manager.get_vector_store()
            logger.info("Retrieved vector store")

            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            logger.info("Created vector store index")

            # Create chat engine with metadata filters and retrieval config
            retrieval_config = self.config.get_retrieval_config()
            logger.info(f"Using retrieval config: {retrieval_config}")

            chat_engine = index.as_chat_engine(
                filters=metadata_filter,
                **retrieval_config
            )
            logger.info("Created chat engine")

            # Format chat history as ChatMessage objects
            formatted_history = [
                ChatMessage(
                    role=self._convert_role(msg["role"]),
                    content=msg["content"]
                )
                for msg in chat_history
            ]
            logger.info(f"Formatted chat history: {len(formatted_history)} messages")

            # Get response
            logger.info("Sending chat request to engine")
            response = await chat_engine.achat(
                message=message,
                chat_history=formatted_history
            )
            logger.info("Received response from chat engine")

            # Handle response
            if hasattr(response, 'response'):
                result = str(response.response)
            elif hasattr(response, 'message'):
                result = str(response.message)
            else:
                result = str(response)

            logger.info(f"Final response length: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            raise ChatError(f"Failed to process chat message: {str(e)}")