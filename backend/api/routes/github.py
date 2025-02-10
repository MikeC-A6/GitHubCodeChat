from fastapi import APIRouter, HTTPException
from backend.services.github_service import GitHubService
from backend.services.embeddings_service import EmbeddingsService
from pydantic import BaseModel

router = APIRouter()
github_service = GitHubService()
embeddings_service = EmbeddingsService()

class RepositoryRequest(BaseModel):
    url: str

@router.post("/process")
async def process_repository(request: RepositoryRequest):
    try:
        # Fetch repository content
        repo_data = await github_service.fetch_repository(request.url)
        
        # Generate embeddings
        embeddings = await embeddings_service.generate_embeddings(repo_data["files"])
        
        return {
            "status": "success",
            "repository": repo_data,
            "embeddings": embeddings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
