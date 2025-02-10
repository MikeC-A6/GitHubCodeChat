from openai import OpenAI
import os
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
from typing import Optional
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        """Initialize the OpenAI client"""
        # Get API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        try:
            # Initialize OpenAI client
            self.client = OpenAI(
                api_key=openai_api_key,
                timeout=60.0
            )
            
            # Initialize vector store service
            self.vector_store = VectorStoreService()
            
            logger.info("EmbeddingsService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingsService: {str(e)}")
            raise

    async def process_repository(
        self,
        repo_id: int,
        files: List[Dict[str, str]],
        status_callback: Optional[callable] = None
    ) -> bool:
        """
        Process an entire repository's files and store embeddings in vector store
        
        Args:
            repo_id: The repository ID (integer)
            files: List of files with name and content
            status_callback: Optional callback to update status
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting embedding process for repository {repo_id}")
            
            # Update status if callback provided
            if status_callback:
                await status_callback("processing", "Started embedding generation")
            
            # Generate embeddings for all files
            embeddings_list = await self.generate_embeddings(files)
            
            # Store vectors in Pinecone using vector store service
            await self.vector_store.upsert_vectors(
                repository_id=repo_id,
                vectors=embeddings_list
            )
            
            logger.info(f"Successfully processed repository {repo_id}")
            
            # Update status if callback provided
            if status_callback:
                await status_callback("completed", "Embedding generation completed")
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing repository {repo_id}: {str(e)}"
            logger.error(error_msg)
            
            # Update status if callback provided
            if status_callback:
                await status_callback("failed", error_msg)
            
            raise

    async def generate_embeddings(self, files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for repository files using OpenAI's text-embedding-3-large model
        """
        embeddings_list = []

        try:
            for file in files:
                # Combine filename and content for context
                content = f"File: {file['name']}\n\nContent:\n{file['content']}"

                # Generate embeddings using OpenAI
                response = await self.client.embeddings.create(
                    model="text-embedding-3-large",
                    input=content,
                    dimensions=3072
                )

                embeddings_list.append({
                    "file_name": file["name"],
                    "embedding": response.data[0].embedding,
                    "content": content
                })

            logger.info(f"Successfully generated embeddings for {len(files)} files")
            return embeddings_list

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def delete_repository_embeddings(self, repo_id: int) -> None:
        """
        Delete all embeddings for a repository
        
        Args:
            repo_id: Repository ID to delete embeddings for
        """
        try:
            await self.vector_store.delete_repository(repo_id)
            logger.info(f"Successfully deleted embeddings for repository {repo_id}")
        except Exception as e:
            logger.error(f"Error deleting repository embeddings: {str(e)}")
            raise