import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.api.health import router as health_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.chat import router as chat_router
from backend.app.api.ingest import router as ingest_router

import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    
    # Automatically start background ingestion of complete transcript collection non-blockingly
    try:
        from backend.app.ingestion.ingest import ingestion_manager
        asyncio.create_task(ingestion_manager.start_background_ingestion())
        logger.info("🚀 Background transcript discovery & indexing task launched non-blockingly.")
    except Exception as e:
        logger.warning(f"Auto-ingestion background launch encountered an issue: {e}")
        
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-stack AI assistant for product & growth teams based on Lenny's Podcast/Newsletter transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(sessions_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(ingest_router, prefix=settings.API_PREFIX)

# Serve Frontend static assets if directory exists
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
