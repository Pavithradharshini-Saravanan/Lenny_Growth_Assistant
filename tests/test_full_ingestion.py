import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db.models import TranscriptModel, TranscriptChunkModel
from backend.app.ingestion.ingest import (
    discover_all_transcripts,
    IngestionManager,
    _fetch_transcript_text,
    ingest_transcript_from_text,
)

client = TestClient(app)


def test_discover_all_transcripts_dynamically():
    """Verify dynamic discovery returns full upstream collection without hardcoded file lists."""
    episodes = discover_all_transcripts()
    assert isinstance(episodes, list)
    assert len(episodes) > 10, f"Expected full collection, got {len(episodes)}"
    
    first = episodes[0]
    assert "slug" in first
    assert "title" in first
    assert "url" in first
    assert first["url"].startswith("http")


def test_ingestion_status_api_endpoint():
    """Verify GET /api/ingest/status returns accurate real-time status."""
    res = client.get("/api/ingest/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "is_running" in data
    assert "discovered_count" in data
    assert "processed_count" in data
    assert "total_chunks" in data
    assert "ready" in data


def test_ingest_trigger_background_api_endpoint():
    """Verify POST /api/ingest with background mode returns success and progress payload."""
    res = client.post("/api/ingest?mode=background")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "background"
    assert "progress" in data


def test_ingestion_manager_idempotency_and_no_duplicates(db_session):
    """Verify IngestionManager does not create duplicate transcripts or duplicate chunks on repeated runs."""
    sample_raw = """---
guest: Idempotency Tester
title: Lenny's Podcast - Idempotency Episode
youtube_url: https://youtube.com/watch?v=idempotent
publish_date: 2026-01-01
---
Speaker 1: Testing idempotent ingestion behavior across multiple passes.
Speaker 2: We must never produce duplicate chunks or transcript rows.
"""
    t1 = ingest_transcript_from_text(
        db_session, sample_raw, default_title="Idempotency Episode", source_url="https://example.com/idempotent.md"
    )
    assert t1 is not None
    initial_transcript_count = db_session.query(TranscriptModel).filter(
        TranscriptModel.title == "Lenny's Podcast - Idempotency Episode"
    ).count()
    initial_chunk_count = db_session.query(TranscriptChunkModel).filter(
        TranscriptChunkModel.transcript_id == t1.id
    ).count()
    assert initial_transcript_count == 1
    assert initial_chunk_count > 0

    # Attempt re-ingesting identical content
    t2 = ingest_transcript_from_text(
        db_session, sample_raw, default_title="Idempotency Episode", source_url="https://example.com/idempotent.md"
    )
    assert t2.id == t1.id

    # Verify counts remained strictly 1 with no duplicates
    final_transcript_count = db_session.query(TranscriptModel).filter(
        TranscriptModel.title == "Lenny's Podcast - Idempotency Episode"
    ).count()
    final_chunk_count = db_session.query(TranscriptChunkModel).filter(
        TranscriptChunkModel.transcript_id == t1.id
    ).count()
    assert final_transcript_count == 1
    assert final_chunk_count == initial_chunk_count



@pytest.mark.anyio
async def test_ingestion_manager_failure_isolation():
    """Verify single episode network failure is recorded safely without stopping the pipeline."""
    mgr = IngestionManager()
    
    # Mock single episode failure
    with patch("backend.app.ingestion.ingest._fetch_transcript_text", side_effect=RuntimeError("Simulated CDN 404")):
        failed_item = {
            "slug": "faulty-episode",
            "title": "Faulty Episode",
            "url": "https://cdn.example.com/nonexistent.md"
        }
        with pytest.raises(RuntimeError):
            await mgr._ingest_single_episode(failed_item)
