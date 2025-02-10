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

@router.post("/generate-embeddings/{repo_id}")
async def generate_embeddings(repo_id: str) -> Dict[str, Any]:
    """
    Step 2: Generate embeddings for a processed repository
    """
    try:
        logger.info(f"Starting embeddings generation for repository ID: {repo_id}")
        
        # Get repository files from database
        logger.info("Fetching repository files from database...")
        files = await db_service.get_repository_files(repo_id)
        
        if not files:
            logger.warning(f"No files found for repository {repo_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No files found for repository {repo_id}"
            )
        
        logger.info(f"Found {len(files)} files to process")
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = await embeddings_service.generate_embeddings(files)
        logger.info(f"Successfully generated embeddings for {len(embeddings)} files")
        
        # Store embeddings in database
        logger.info("Storing embeddings in database...")
        await db_service.store_embeddings(repo_id, embeddings)
        logger.info("Successfully stored embeddings")
        
        return {
            "status": "success",
            "message": "Embeddings generated and stored successfully",
            "repository_id": repo_id
        }
    except HTTPException as e:
        logger.error(f"HTTP error in embeddings generation: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embeddings: {str(e)}"
        )