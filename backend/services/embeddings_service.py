from openai import OpenAI
import os
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        """Initialize the OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        try:
            self.client = OpenAI(
                api_key=api_key,
                timeout=60.0  # Set a reasonable timeout
            )
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
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
                    dimensions=3072  # Match Pinecone's dimension setting
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