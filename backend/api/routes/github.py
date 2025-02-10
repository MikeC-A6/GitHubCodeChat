from fastapi import APIRouter, HTTPException
from backend.services.github_service import GitHubService
from backend.services.embeddings_service import EmbeddingsService
from backend.services.db_service import DatabaseService
from pydantic import BaseModel
from typing import Dict, Any, List
import os

router = APIRouter()
github_service = GitHubService()
embeddings_service = EmbeddingsService()
db_service = DatabaseService()

class RepositoryRequest(BaseModel):
    url: str

@router.get("/repositories")
async def get_repositories() -> List[Dict[str, Any]]:
    """
    Get all repositories
    """
    try:
        repositories = await db_service.get_repositories()
        return repositories
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch repositories: {str(e)}"
        )

@router.post("/process")
async def process_repository(request: RepositoryRequest) -> Dict[str, Any]:
    """
    Step 1: Process repository - fetch from GitHub and store in PostgreSQL
    """
    try:
        # Fetch repository data from GitHub
        repo_data = await github_service.get_repository_data(request.url)
        
        # Store in database
        repo_id = await db_service.store_repository(repo_data)
        
        return {
            "status": "success",
            "message": "Repository processed and stored successfully",
            "repository_id": repo_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process repository: {str(e)}"
        )

@router.post("/generate-embeddings/{repo_id}")
async def generate_embeddings(repo_id: str) -> Dict[str, Any]:
    """
    Step 2: Generate embeddings for a processed repository
    """
    try:
        # Get repository files from database
        files = await db_service.get_repository_files(repo_id)
        
        if not files:
            raise HTTPException(
                status_code=404,
                detail=f"No files found for repository {repo_id}"
            )
        
        # Generate embeddings
        embeddings = await embeddings_service.generate_embeddings(files)
        
        # Store embeddings in database
        await db_service.store_embeddings(repo_id, embeddings)
        
        return {
            "status": "success",
            "message": "Embeddings generated and stored successfully",
            "repository_id": repo_id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embeddings: {str(e)}"
        )