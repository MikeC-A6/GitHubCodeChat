from openai import OpenAI
import os

class EmbeddingsService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_embeddings(self, files: list[dict]):
        embeddings = []
        
        for file in files:
            content = f"{file['name']}\n{file['content']}"
            
            response = await self.client.embeddings.create(
                model="text-embedding-3-large",
                input=content
            )
            
            embeddings.append({
                "file_name": file["name"],
                "embedding": response.data[0].embedding
            })
        
        return embeddings
