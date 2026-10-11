from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.ingestion.ingest import run_sample_ingestion

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

@router.post("")
def trigger_ingestion(db: Session = Depends(get_db)):
    count = run_sample_ingestion(db=db)
    return {
        "status": "success",
        "transcripts_ingested": count,
        "message": f"Successfully ingested {count} transcripts into the database index."
    }
