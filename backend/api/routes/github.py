from fastapi import APIRouter, HTTPException
from backend.services.github_service import GitHubService
from backend.services.embeddings_service import EmbeddingsService
from pydantic import BaseModel
from typing import Dict, Any
import os

router = APIRouter()
github_service = GitHubService()
embeddings_service = EmbeddingsService()

class RepositoryRequest(BaseModel):
    url: str

@router.post("/process")
async def process_repository(request: RepositoryRequest) -> Dict[str, Any]:
    """
    Process a GitHub repository:
    1. Fetch repository content using GitHub GraphQL API
    2. Generate embeddings for the code files
    3. Store results in the database
    """
    try:
        # Fetch repository content
        repo_data = await github_service.fetch_repository(request.url)
        
        if not repo_data.get("files"):
            raise HTTPException(
                status_code=400,
                detail="No files found in repository"
            )

        # Generate embeddings
        embeddings = await embeddings_service.generate_embeddings(repo_data["files"])

        return {
            "status": "success",
            "repository": repo_data,
            "embeddings": embeddings
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process repository: {str(e)}"
        )