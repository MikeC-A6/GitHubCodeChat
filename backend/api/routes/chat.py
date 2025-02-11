from fastapi import APIRouter, HTTPException
from backend.services.llama import LlamaService
from pydantic import BaseModel
from typing import List, Dict, Any

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
        if not request.repository_ids:
            raise HTTPException(
                status_code=400,
                detail="At least one repository ID must be provided"
            )

        response = await llama_service.chat(
            repository_ids=request.repository_ids,
            message=request.message,
            chat_history=request.chat_history
        )

        return {"response": response}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )