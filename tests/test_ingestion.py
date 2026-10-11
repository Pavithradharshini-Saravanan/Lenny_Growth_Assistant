import pytest
from backend.app.ingestion.ingest import (
    parse_transcript_markdown,
    chunk_transcript_text,
    ingest_transcript_from_text,
)
from backend.app.db.models import TranscriptModel, TranscriptChunkModel
from sqlalchemy import select

SAMPLE_MARKDOWN = """---
guest: Brian Chesky
title: Brian Chesky's new playbook
youtube_url: https://www.youtube.com/watch?v=4ef0juAMqoE
publish_date: 2023-11-12
keywords:
- growth
- metrics
---

# Brian Chesky's new playbook

Brian Chesky (00:00:00):
Way too many founders apologize for how they want to run the company. They find some midpoint between how they want to run a company and how the people they lead want to run the company.

Lenny (00:01:01):
Today my guest is Brian Chesky. Brian is the CEO and co-founder of Airbnb.
"""

def test_parse_transcript_markdown():
    frontmatter, body = parse_transcript_markdown(SAMPLE_MARKDOWN)
    assert frontmatter["guest"] == "Brian Chesky"
    assert frontmatter["title"] == "Brian Chesky's new playbook"
    assert "founders apologize" in body

def test_chunk_transcript_text():
    frontmatter, body = parse_transcript_markdown(SAMPLE_MARKDOWN)
    chunks = chunk_transcript_text(body, max_chunk_words=50)
    assert len(chunks) >= 1
    assert "founders" in chunks[0]["content"]

def test_ingest_transcript_persistence(db_session):
    transcript = ingest_transcript_from_text(db_session, SAMPLE_MARKDOWN)
    assert transcript.id is not None
    assert transcript.title == "Brian Chesky's new playbook"

    # Query DB chunks
    chunks = db_session.scalars(select(TranscriptChunkModel).where(TranscriptChunkModel.transcript_id == transcript.id)).all()
    assert len(chunks) > 0
    assert chunks[0].chunk_metadata["guest"] == "Brian Chesky"

def test_ingest_deduplication(db_session):
    """Verify re-ingesting identical transcript returns existing model without duplicating records."""
    t1 = ingest_transcript_from_text(db_session, SAMPLE_MARKDOWN)
    t2 = ingest_transcript_from_text(db_session, SAMPLE_MARKDOWN)
    assert t1.id == t2.id

    all_transcripts = db_session.scalars(select(TranscriptModel).where(TranscriptModel.title == "Brian Chesky's new playbook")).all()
    assert len(all_transcripts) == 1

def test_ingestion_followed_by_retrieval_same_db(db_session):
    """Regression test verifying ingestion immediately enables grounded retrieval for questions."""
    from backend.app.services.retrieval_service import RetrievalService
    ingest_transcript_from_text(db_session, SAMPLE_MARKDOWN)

    res = RetrievalService.search_chunks(db_session, query="What did Brian Chesky say about founders?", top_k=3)
    assert res["empty_result"] is False
    assert len(res["results"]) > 0
    assert res["results"][0]["guest"] == "Brian Chesky"
