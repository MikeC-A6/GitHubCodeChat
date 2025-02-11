from fastapi import APIRouter, HTTPException
from backend.services.llama import LlamaService
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
llama_service = LlamaService()

class ChatRequest(BaseModel):
    repository_ids: List[int]
    message: str
    chat_history: List[Dict[str, str]]

@router.post("/message")
async def chat_message(request: ChatRequest) -> Dict[str, str]:
    """
    Process a chat message using LlamaIndex and Gemini
    """
    try:
        logger.info(f"Received chat request: {request.repository_ids}")

        if not request.repository_ids:
            logger.error("No repository IDs provided")
            raise HTTPException(
                status_code=400,
                detail="At least one repository ID must be provided"
            )

        logger.info("Processing chat request...")
        response = await llama_service.chat(
            repository_ids=request.repository_ids,
            message=request.message,
            chat_history=request.chat_history
        )
        logger.info("Chat request processed successfully")

        return {"response": response}

    except Exception as e:
        logger.error(f"Failed to process chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )