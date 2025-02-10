from openai import OpenAI
import os
from typing import List, Dict, Any
import json

class EmbeddingsService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
                    encoding_format="float"
                )

                embeddings_list.append({
                    "file_name": file["name"],
                    "embedding": response.data[0].embedding,
                    "content": content
                })

            return embeddings_list

        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise