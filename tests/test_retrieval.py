import pytest
from backend.app.ingestion.ingest import ingest_transcript_from_text
from backend.app.services.retrieval_service import RetrievalService
from backend.app.tools.base import search_transcripts_domain

EPISODE_1 = """---
guest: Brian Chesky
title: Brian Chesky's new playbook
youtube_url: https://www.youtube.com/watch?v=4ef0juAMqoE
---
Brian Chesky (00:05:00):
We combined product management with product marketing at Airbnb. You cannot build a great product unless you know how to talk about the product. We eliminated traditional performance marketing arbitrage and focused on brand education.
"""

EPISODE_2 = """---
guest: Elena Verna
title: B2B Growth and PLG Masterclass
youtube_url: https://www.youtube.com/watch?v=elena_verna_123
---
Elena Verna (00:02:00):
Product-led growth (PLG) requires reducing onboarding friction so users reach the aha moment immediately before paywalls or signup forms.
"""

@pytest.fixture
def populated_db(db_session):
    ingest_transcript_from_text(db_session, EPISODE_1)
    ingest_transcript_from_text(db_session, EPISODE_2)
    return db_session

def test_grounded_retrieval_success(populated_db):
    res = RetrievalService.search_chunks(populated_db, "product management and marketing at Airbnb", top_k=3)
    assert res["empty_result"] is False
    assert len(res["results"]) > 0
    top = res["results"][0]
    assert top["guest"] == "Brian Chesky"
    assert "combined product management" in top["content"]
    assert top["source_url"] == "https://www.youtube.com/watch?v=4ef0juAMqoE"

def test_paraphrased_query_retrieval(populated_db):
    res = search_transcripts_domain(populated_db, query="reducing friction during initial user onboarding experience", top_k=3)
    assert res["empty_result"] is False
    assert len(res["results"]) > 0
    top = res["results"][0]
    assert top["guest"] == "Elena Verna"
    assert "onboarding friction" in top["content"]

def test_unsupported_out_of_corpus_query(populated_db):
    res = RetrievalService.search_chunks(populated_db, "quantum computing semiconductor photolithography", top_k=3)
    assert res["empty_result"] is True
    assert len(res["results"]) == 0
    assert "empty_result" in res

def test_empty_database_retrieval(db_session):
    res = RetrievalService.search_chunks(db_session, "PLG growth metrics", top_k=3)
    assert res["empty_result"] is True
    assert len(res["results"]) == 0

# --- REGRESSION TESTS FOR TYPE COERCION & POSITION/KEYWORD ARGS ---
def test_regression_int_query_handling(populated_db):
    """Regression test verifying numeric query inputs do not raise 'int object has no attribute lower'."""
    # Test integer query
    res = search_transcripts_domain(populated_db, query=2023, top_k=5)
    assert "empty_result" in res
    assert isinstance(res["results"], list)

    # Test string top_k
    res_topk_str = search_transcripts_domain(populated_db, query="product marketing", top_k="5")
    assert res_topk_str["empty_result"] is False

def test_regression_search_transcripts_domain_kwargs_calling(populated_db):
    """Regression test for position vs keyword argument calling pattern."""
    res = search_transcripts_domain(query="Brian Chesky product marketing", top_k=5)
    assert res["empty_result"] is False
    assert res["results"][0]["guest"] == "Brian Chesky"
