from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.ingestion.ingest import run_sample_ingestion, ingestion_manager

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.get("/status")
def get_ingestion_status(db: Session = Depends(get_db)):
    """Return real-time transcript discovery and indexing progress."""
    return ingestion_manager.get_status(db=db)

@router.post("")
async def trigger_ingestion(
    mode: str = Query("background", description="'background' for full upstream library or 'sample' for initial seed"),
    max_batch: int | None = Query(None, description="Optional batch size limit"),
    db: Session = Depends(get_db)
):
    """
    Trigger transcript ingestion.
    Default mode 'background' starts non-blocking background discovery & indexing of the complete upstream library.
    Mode 'sample' runs synchronous ingestion of initial seed episodes.
    """
    if mode == "sample":
        count = run_sample_ingestion(db=db)
        return {
            "status": "success",
            "mode": "sample",
            "transcripts_ingested": count,
            "message": f"Successfully ingested {count} seed transcripts into the database index."
        }

    # Background ingestion of complete library
    await ingestion_manager.start_background_ingestion(max_batch=max_batch)
    return {
        "status": "success",
        "mode": "background",
        "message": "Background transcript discovery and ingestion started.",
        "progress": ingestion_manager.get_status(db=db)
    }
