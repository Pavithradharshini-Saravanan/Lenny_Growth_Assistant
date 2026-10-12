import urllib.request
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.config import settings
from backend.app.db.database import get_db
from backend.app.schemas.session import HealthResponse, ConfigResponse

router = APIRouter(tags=["Health & Config"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_alive = False
    try:
        db.execute(text("SELECT 1"))
        db_alive = True
    except Exception:
        db_alive = False

    ollama_alive = False
    try:
        req = urllib.request.urlopen(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=10)
        ollama_alive = req.status == 200
    except Exception:
        ollama_alive = False

    status_str = "ok" if (db_alive and (settings.PROVIDER_TYPE == "cloud" or ollama_alive)) else "degraded"

    return HealthResponse(
        status=status_str,
        database=db_alive,
        ollama=ollama_alive,
        version="1.0.0"
    )

@router.get("/config", response_model=ConfigResponse)
def get_config():
    has_anthropic = bool(settings.ANTHROPIC_API_KEY)
    has_gemini = bool(settings.GEMINI_API_KEY)

    if settings.PROVIDER_TYPE == "ollama":
        active_model = settings.OLLAMA_MODEL
    elif settings.PROVIDER_TYPE in ("gemini", "google"):
        active_model = settings.GEMINI_MODEL
    else:
        active_model = settings.CLOUD_MODEL

    return ConfigResponse(
        active_provider=settings.PROVIDER_TYPE,
        active_model=active_model,
        ollama_url=settings.OLLAMA_BASE_URL,
        cloud_key_configured=has_anthropic,
        gemini_key_configured=has_gemini,
        supported_providers=["ollama", "cloud", "gemini"],
        sdk_integration="Anthropic Claude Agent SDK & Google Gemini (REST API)"
    )
