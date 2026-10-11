from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.services.session_service import SessionService
from backend.app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    MessageResponse,
    ArtifactResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    db_session = SessionService.create_session(db, session_in)
    return SessionResponse(
        id=db_session.id,
        title=db_session.title,
        provider=db_session.provider,
        model=db_session.model,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        message_count=0
    )

@router.get("", response_model=list[SessionResponse])
def list_sessions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    results = SessionService.list_sessions(db, limit, offset)
    response_list = []
    for db_session, count in results:
        response_list.append(SessionResponse(
            id=db_session.id,
            title=db_session.title,
            provider=db_session.provider,
            model=db_session.model,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            message_count=count
        ))
    return response_list

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = SessionService.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    messages = SessionService.get_session_messages(db, session_id)
    return SessionResponse(
        id=db_session.id,
        title=db_session.title,
        provider=db_session.provider,
        model=db_session.model,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        message_count=len(messages)
    )

@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(session_id: str, session_in: SessionUpdate, db: Session = Depends(get_db)):
    db_session = SessionService.update_session(db, session_id, session_in)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    messages = SessionService.get_session_messages(db, session_id)
    return SessionResponse(
        id=db_session.id,
        title=db_session.title,
        provider=db_session.provider,
        model=db_session.model,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        message_count=len(messages)
    )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    success = SessionService.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return None

@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    db_session = SessionService.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return SessionService.get_session_messages(db, session_id)

@router.get("/{session_id}/artifacts", response_model=list[ArtifactResponse])
def get_session_artifacts(session_id: str, db: Session = Depends(get_db)):
    db_session = SessionService.get_session(db, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return SessionService.get_session_artifacts(db, session_id)
