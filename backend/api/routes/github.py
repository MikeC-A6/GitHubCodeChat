from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from backend.services.github_service import GitHubService
from backend.services.embeddings_service import EmbeddingsService
from backend.services.db_service import DatabaseService
from pydantic import BaseModel
from typing import Dict, Any, List
import os
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()
github_service = GitHubService()
embeddings_service = EmbeddingsService()
db_service = DatabaseService()

class RepositoryRequest(BaseModel):
    url: str

@router.get("/repositories")
async def get_repositories() -> JSONResponse:
    """
    Get all repositories
    """
    try:
        repositories = await db_service.get_repositories()
        
        # Convert datetime objects to ISO format strings
        for repo in repositories:
            if repo.get('processed_at'):
                repo['processed_at'] = repo['processed_at'].isoformat()
            if repo.get('created_at'):
                repo['created_at'] = repo['created_at'].isoformat()
                
        return JSONResponse(content=repositories)
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@router.post("/process")
async def process_repository(request: RepositoryRequest) -> JSONResponse:
    """
    Step 1: Process repository - fetch from GitHub and store in PostgreSQL
    """
    try:
        logger.info("=== Starting repository processing ===")
        logger.info(f"Received request with URL: {request.url}")
        logger.info(f"Request data: {request.dict()}")
        
        # Fetch repository data from GitHub
        logger.info("Attempting to fetch repository data from GitHub...")
        try:
            repo_data = await github_service.get_repository_data(request.url)
            logger.info(f"Successfully fetched repository data: {repo_data.get('name', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to fetch repository data: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"GitHub fetch failed: {str(e)}"}
            )
        
        # Store in database
        logger.info("Attempting to store repository data in database...")
        try:
            repo_id = await db_service.store_repository(repo_data)
            logger.info(f"Successfully stored repository with ID: {repo_id}")
        except Exception as e:
            logger.error(f"Failed to store repository: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"Database storage failed: {str(e)}"}
            )
        
        logger.info("=== Repository processing completed successfully ===")
        return JSONResponse(content={
            "status": "success",
            "message": "Repository processed and stored successfully",
            "repository_id": repo_id
        })
    except Exception as e:
        logger.error(f"=== Repository processing failed ===")
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to process repository: {str(e)}"}
        )

@router.post("/repositories/{repo_id}/embed")
async def generate_embeddings(repo_id: int) -> Dict[str, Any]:
    """
    Generate embeddings for a processed repository and store them in the vector store
    """
    try:
        logger.info(f"Starting embeddings generation for repository ID: {repo_id}")
        
        # Get repository from database
        repository = await db_service.get_repository(repo_id)
        if not repository:
            logger.warning(f"Repository {repo_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Repository {repo_id} not found"
            )
        
        # Check if repository is already being processed
        if repository.get("embedding_status") == "processing":
            logger.warning(f"Repository {repo_id} is already being processed")
            raise HTTPException(
                status_code=400,
                detail=f"Repository {repo_id} is already being processed"
            )
        
        # Get repository files
        logger.info("Fetching repository files from database...")
        files = repository.get("files", [])
        if not files:
            logger.warning(f"No files found for repository {repo_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No files found for repository {repo_id}"
            )
        
        logger.info(f"Found {len(files)} files to process")
        
        # Define status update callback
        async def update_status(status: str, message: str):
            await db_service.update_embedding_status(
                repo_id=repo_id,
                status=status,
                error_message=message if status == "failed" else None
            )
        
        # Process repository and generate embeddings
        logger.info("Processing repository and generating embeddings...")
        await embeddings_service.process_repository(
            repo_id=repo_id,
            files=files,
            status_callback=update_status
        )
        
        return {
            "status": "success",
            "message": "Embedding generation started successfully",
            "repository_id": repo_id
        }
        
    except HTTPException as e:
        logger.error(f"HTTP error in embeddings generation: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
        # Update status in database
        try:
            await db_service.update_embedding_status(
                repo_id=repo_id,
                status="failed",
                error_message=str(e)
            )
        except Exception as status_e:
            logger.error(f"Failed to update error status: {str(status_e)}")
            
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embeddings: {str(e)}"
        )

@router.get("/repositories/{repo_id}/embedding-status")
async def get_embedding_status(repo_id: int) -> Dict[str, Any]:
    """
    Get the current embedding status for a repository
    """
    try:
        repository = await db_service.get_repository(repo_id)
        if not repository:
            raise HTTPException(
                status_code=404,
                detail=f"Repository {repo_id} not found"
            )
            
        # Convert datetime objects to ISO format strings
        if repository.get('processed_at'):
            repository['processed_at'] = repository['processed_at'].isoformat()
        if repository.get('created_at'):
            repository['created_at'] = repository['created_at'].isoformat()
            
        return {
            "status": repository.get("status", "pending"),
            "error": repository.get("error_message"),
            "repository_id": repo_id,
            "vectorized": repository.get("vectorized", False),
            "processed_at": repository.get("processed_at")
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching embedding status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch embedding status: {str(e)}"
        )