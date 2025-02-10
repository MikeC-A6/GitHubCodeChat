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
    Process a GitHub repository:
    1. Fetch repository content using GitHub GraphQL API
    2. Store repository data in PostgreSQL
    3. Generate embeddings for the code files
    4. Store results in Pinecone
    """
    try:
        # Fetch repository content
        repo_data = await github_service.fetch_repository(request.url)
        
        if not repo_data.get("files"):
            raise HTTPException(
                status_code=400,
                detail="No files found in repository"
            )

        # Store repository in database
        repository = await db_service.create_repository({
            "url": request.url,
            "name": repo_data["name"],
            "owner": repo_data["owner"],
            "description": repo_data["description"],
            "files": repo_data["files"],
            "status": "pending",
            "branch": repo_data["branch"],
            "path": repo_data["path"],
            "vectorized": False
        })

        # Generate embeddings (we'll integrate with Pinecone in the next phase)
        embeddings = await embeddings_service.generate_embeddings(repo_data["files"])

        return {
            "status": "success",
            "repository": repository,
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