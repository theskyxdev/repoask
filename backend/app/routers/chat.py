from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.models.schemas import ChatQueryRequest, ChatResponse, ChatMessage
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def query_repository(request: ChatQueryRequest):
    try:
        return chat_service.query_repo(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}", response_model=List[ChatMessage])
def get_conversation_history(conversation_id: str):
    return chat_service.get_conversation_history(conversation_id)
