import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.services.session_service import SessionService
from backend.app.agent.dispatcher import get_agent_adapter
from backend.app.agent.base import ConfigurationError
from backend.app.schemas.session import ChatRequest, ChatResponse, MessageCreate, SourceCitation, SessionUpdate
from backend.app.db.models import ArtifactModel, MessageModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    logger.info(f"Received chat request for session '{request.session_id}': prompt='{request.message[:50]}'")

    # 1. Verify session exists
    db_session = SessionService.get_session(db, request.session_id)
    if not db_session:
        logger.warning(f"Session '{request.session_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{request.session_id}' not found."
        )

    # Determine provider/model override if supplied
    chosen_provider = (request.provider or db_session.provider).lower().strip()
    if request.model:
        chosen_model = request.model
    elif request.provider and request.provider != db_session.provider:
        # Provider switched: use appropriate default model for the new provider
        if chosen_provider in ("gemini", "google"):
            chosen_model = settings.GEMINI_MODEL
        elif chosen_provider == "cloud":
            chosen_model = settings.CLOUD_MODEL
        else:
            chosen_model = settings.OLLAMA_MODEL
    else:
        # Same provider: use session model if valid for this provider, else fallback to configured default
        if chosen_provider in ("gemini", "google"):
            chosen_model = db_session.model if "gemini" in db_session.model.lower() else settings.GEMINI_MODEL
        elif chosen_provider == "cloud":
            chosen_model = db_session.model if "claude" in db_session.model.lower() else settings.CLOUD_MODEL
        elif chosen_provider == "ollama":
            # For ollama, keep session model if it's not a cloud model name, else use settings.OLLAMA_MODEL
            is_cloud_name = any(k in db_session.model.lower() for k in ("gemini", "claude", "gpt"))
            chosen_model = settings.OLLAMA_MODEL if is_cloud_name else db_session.model
        else:
            chosen_model = db_session.model

    # 2. Get history & persist user message
    user_msg_in = MessageCreate(role="user", content=request.message)
    user_msg = SessionService.add_message(db, request.session_id, user_msg_in)

    history_records = SessionService.get_session_messages(db, request.session_id)
    # Exclude current message from history and bound to recent sliding window (last 8 messages)
    history_payload = [
        {"role": m.role, "content": m.content}
        for m in history_records[:-1][-8:]
    ]

    # 3. Instantiate Agent Adapter & Execute
    try:
        adapter = get_agent_adapter(provider=chosen_provider, model=chosen_model)
        result = await adapter.run_agent(
            prompt=request.message,
            history=history_payload,
            session_id=request.session_id
        )
    except ConfigurationError as ce:
        logger.error(f"Configuration error during agent execution: {ce}")
        # Clean up orphan user message so history isn't corrupted
        db.delete(user_msg)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ce)
        )
    except Exception as e:
        logger.exception(f"Unhandled exception during agent execution for session '{request.session_id}': {e}")
        # Clean up orphan user message so history isn't corrupted
        db.delete(user_msg)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}"
        )

    # 4. Process sources & persist assistant message
    try:
        sources_raw = result.get("sources", [])
        sources_models = [
            SourceCitation(
                title=s.get("title", "Unknown Source"),
                source_url=s.get("source_url"),
                chunk_id=s.get("chunk_id"),
                score=s.get("score")
            )
            for s in sources_raw
        ]

        asst_msg_in = MessageCreate(
            role="assistant",
            content=result.get("content", ""),
            sources=sources_models
        )
        asst_msg = SessionService.add_message(db, request.session_id, asst_msg_in)

        # 5. Persist artifact if created
        artifact_data = result.get("artifact")
        artifact_resp = None
        if artifact_data and isinstance(artifact_data, dict):
            db_artifact = ArtifactModel(
                session_id=request.session_id,
                message_id=asst_msg.id,
                title=artifact_data.get("title", "Untitled Artifact"),
                artifact_type=artifact_data.get("artifact_type", "markdown"),
                content=artifact_data.get("content", "")
            )
            db.add(db_artifact)
            db.commit()
            db.refresh(db_artifact)

            artifact_resp = {
                "id": db_artifact.id,
                "session_id": db_artifact.session_id,
                "message_id": db_artifact.message_id,
                "title": db_artifact.title,
                "artifact_type": db_artifact.artifact_type,
                "content": db_artifact.content,
                "created_at": db_artifact.created_at
            }

        # Auto-update session title if it's default
        if db_session.title in ["New Chat", "Untitled"]:
            new_title = request.message[:35] + ("..." if len(request.message) > 35 else "")
            SessionService.update_session(db, request.session_id, SessionUpdate(title=new_title))

        return ChatResponse(
            id=asst_msg.id,
            session_id=request.session_id,
            role="assistant",
            content=asst_msg.content,
            sources=sources_models,
            artifact=artifact_resp,
            provider_used=result.get("provider_used", chosen_provider),
            model_used=result.get("model_used", chosen_model)
        )
    except Exception as e:
        logger.exception(f"Error persisting assistant message or updating session: {e}")
        db.delete(user_msg)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response persistence error: {str(e)}"
        )

