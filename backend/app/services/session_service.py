from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.app.db.models import SessionModel, MessageModel, ArtifactModel
from backend.app.schemas.session import SessionCreate, SessionUpdate, MessageCreate
from backend.app.config import settings

class SessionService:
    @staticmethod
    def create_session(db: Session, session_in: SessionCreate) -> SessionModel:
        chosen_model = session_in.model
        if not chosen_model:
            prov = (session_in.provider or "ollama").lower()
            if prov == "ollama":
                chosen_model = settings.OLLAMA_MODEL
            elif prov in ("gemini", "google"):
                chosen_model = settings.GEMINI_MODEL
            elif prov == "cloud":
                chosen_model = settings.CLOUD_MODEL
            else:
                chosen_model = settings.OLLAMA_MODEL

        db_session = SessionModel(
            title=session_in.title,
            provider=session_in.provider,
            model=chosen_model
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def get_session(db: Session, session_id: str) -> SessionModel | None:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        return db.scalar(stmt)

    @staticmethod
    def list_sessions(db: Session, limit: int = 50, offset: int = 0) -> list[tuple[SessionModel, int]]:
        stmt = (
            select(SessionModel, func.count(MessageModel.id).label("message_count"))
            .outerjoin(MessageModel, SessionModel.id == MessageModel.session_id)
            .group_by(SessionModel.id)
            .order_by(SessionModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.execute(stmt).all()

    @staticmethod
    def update_session(db: Session, session_id: str, session_in: SessionUpdate) -> SessionModel | None:
        db_session = SessionService.get_session(db, session_id)
        if not db_session:
            return None
        if session_in.title is not None:
            db_session.title = session_in.title
        if session_in.provider is not None:
            db_session.provider = session_in.provider
        if session_in.model is not None:
            db_session.model = session_in.model
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        db_session = SessionService.get_session(db, session_id)
        if not db_session:
            return False
        db.delete(db_session)
        db.commit()
        return True

    @staticmethod
    def add_message(db: Session, session_id: str, message_in: MessageCreate) -> MessageModel:
        sources_data = [s.model_dump() for s in message_in.sources] if message_in.sources else []
        db_message = MessageModel(
            session_id=session_id,
            role=message_in.role,
            content=message_in.content,
            sources=sources_data
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> list[MessageModel]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_session_artifacts(db: Session, session_id: str) -> list[ArtifactModel]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.session_id == session_id)
            .order_by(ArtifactModel.created_at.desc())
        )
        return list(db.scalars(stmt).all())
