import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status

from backend.app.db.database import SessionLocal
from backend.app.db.models import TranscriptModel, TranscriptChunkModel
from backend.app.services.retrieval_service import RetrievalService
from backend.app.schemas.session import SessionCreate

@pytest.fixture
def seeded_db(db_session):
    """Seed test database with the 4 canonical podcast transcripts (217 chunks)."""
    prod_db = SessionLocal()
    try:
        transcripts = prod_db.query(TranscriptModel).all()
        for t in transcripts:
            new_t = TranscriptModel(
                id=t.id,
                title=t.title,
                source_url=t.source_url,
                raw_text=t.raw_text
            )
            db_session.add(new_t)
            for c in t.chunks:
                new_c = TranscriptChunkModel(
                    id=c.id,
                    transcript_id=c.transcript_id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    speaker=c.speaker,
                    chunk_metadata=c.chunk_metadata
                )
                db_session.add(new_c)
        db_session.commit()
    finally:
        prod_db.close()
    return db_session


# --- TEST 1: The 4 Canonical Grounded Questions ---

def test_brian_chesky_release_cycles_and_roadmap_retrieval(seeded_db):
    query = "How does Airbnb structure its release cycles and product roadmap according to Brian Chesky?"
    res = RetrievalService.search_chunks(seeded_db, query, top_k=5)

    assert res["empty_result"] is False
    assert len(res["results"]) > 0

    top_result = res["results"][0]
    assert "Brian Chesky" in (top_result.get("guest") or top_result.get("title"))

    # Verify that the release cycles and roadmap evidence is present across top chunks
    combined_content = " ".join([r["content"].lower() for r in res["results"]])
    assert "release" in combined_content
    assert "roadmap" in combined_content or "product plan" in combined_content


def test_shreyas_doshi_execution_vs_strategy_retrieval(seeded_db):
    query = "Why does Shreyas Doshi say that most execution problems are really strategy problems?"
    res = RetrievalService.search_chunks(seeded_db, query, top_k=5)

    assert res["empty_result"] is False
    assert len(res["results"]) > 0

    top_result = res["results"][0]
    assert "Shreyas Doshi" in (top_result.get("guest") or top_result.get("title"))

    combined_content = " ".join([r["content"].lower() for r in res["results"]])
    assert "execution problems" in combined_content
    assert "strategy problems" in combined_content


def test_marty_cagan_feature_teams_vs_empowered_teams_no_pollution(seeded_db):
    query = "What is the difference between feature teams and empowered product teams according to Marty Cagan?"
    res = RetrievalService.search_chunks(seeded_db, query, top_k=5)

    assert res["empty_result"] is False
    assert len(res["results"]) > 0

    # Ensure all top results are from Marty Cagan's episode, with NO cross-episode pollution
    for r in res["results"]:
        guest = r.get("guest") or ""
        title = r.get("title") or ""
        assert "Marty Cagan" in guest or "Marty Cagan" in title
        assert "Brian Chesky" not in guest
        assert "Elena Verna" not in guest

    combined_content = " ".join([r["content"].lower() for r in res["results"]])
    assert "empowered" in combined_content
    assert "feature team" in combined_content or "teams" in combined_content


def test_elena_verna_onboarding_friction_retrieval(seeded_db):
    query = "What does Elena Verna say about reducing onboarding friction in product-led growth?"
    res = RetrievalService.search_chunks(seeded_db, query, top_k=5)

    assert res["empty_result"] is False
    assert len(res["results"]) > 0

    top_result = res["results"][0]
    assert "Elena Verna" in (top_result.get("guest") or top_result.get("title"))

    # Top results must capture the key discussion on simplifying onboarding and friction
    combined_content = " ".join([r["content"].lower() for r in res["results"]])
    assert "friction" in combined_content
    assert "onboarding" in combined_content or "simplif" in combined_content


# --- TEST 2: Paraphrased Queries ---

@pytest.mark.parametrize("query,expected_guest,expected_keyword", [
    (
        "How often does Airbnb ship new products and plan its roadmaps per Chesky?",
        "Brian Chesky",
        "release"
    ),
    (
        "Why are operational breakdowns usually strategic failures according to Doshi?",
        "Shreyas Doshi",
        "execution problems"
    ),
    (
        "What separates feature factories from empowered teams in Marty Cagan's view?",
        "Marty Cagan",
        "empowered"
    ),
    (
        "Elena Verna's perspective on simplifying signup and onboarding steps in PLG",
        "Elena Verna",
        "onboarding"
    )
])
def test_paraphrased_questions_retrieval(seeded_db, query, expected_guest, expected_keyword):
    res = RetrievalService.search_chunks(seeded_db, query, top_k=3)
    assert res["empty_result"] is False
    assert len(res["results"]) > 0

    top_result = res["results"][0]
    title_or_guest = f"{top_result.get('guest', '')} {top_result.get('title', '')}"
    assert expected_guest in title_or_guest

    combined = " ".join([r["content"].lower() for r in res["results"]])
    assert expected_keyword in combined


# --- TEST 3: Out-of-Corpus / Unsupported Query ---

def test_unsupported_out_of_corpus_query_returns_empty(seeded_db):
    query = "How does quantum photolithography improve semiconductor yield in EUV machines?"
    res = RetrievalService.search_chunks(seeded_db, query, top_k=5)

    assert res["empty_result"] is True
    assert len(res["results"]) == 0
    assert "message" in res


# --- TEST 4: Chat API Turn Lifecycle (New Chat vs Existing Chat) ---

def test_chat_turn_lifecycle_and_session_consistency(client, seeded_db):
    # 1. Create Session
    create_resp = client.post("/api/sessions", json={"title": "New Chat", "provider": "ollama"})
    assert create_resp.status_code == status.HTTP_201_CREATED
    session_id = create_resp.json()["id"]

    mock_result_turn1 = {
        "content": "According to Brian Chesky, Airbnb operates on a rolling two-year product roadmap with major releases.",
        "sources": [
            {
                "title": "Brian Chesky's new playbook",
                "source_url": "https://www.youtube.com/watch?v=4ef0juAMqoE",
                "chunk_id": "chunk_chesky_1",
                "score": 18.5
            }
        ],
        "artifact": None,
        "provider_used": "ollama",
        "model_used": "qwen2.5:3b"
    }

    # 2. First Turn
    with patch("backend.app.api.chat.get_agent_adapter") as mock_get_adapter:
        mock_adapter = AsyncMock()
        mock_adapter.run_agent.return_value = mock_result_turn1
        mock_get_adapter.return_value = mock_adapter

        turn1_resp = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "How does Airbnb structure its release cycles?",
            "provider": "ollama"
        })

        assert turn1_resp.status_code == status.HTTP_200_OK
        data1 = turn1_resp.json()
        assert data1["role"] == "assistant"
        assert len(data1["sources"]) == 1
        assert data1["sources"][0]["title"] == "Brian Chesky's new playbook"

    # 3. Second Turn in Existing Session
    mock_result_turn2 = {
        "content": "Brian Chesky also notes that releases occur in May and November.",
        "sources": [
            {
                "title": "Brian Chesky's new playbook",
                "source_url": "https://www.youtube.com/watch?v=4ef0juAMqoE",
                "chunk_id": "chunk_chesky_2",
                "score": 15.2
            }
        ],
        "artifact": None,
        "provider_used": "ollama",
        "model_used": "qwen2.5:3b"
    }

    with patch("backend.app.api.chat.get_agent_adapter") as mock_get_adapter:
        mock_adapter = AsyncMock()
        mock_adapter.run_agent.return_value = mock_result_turn2
        mock_get_adapter.return_value = mock_adapter

        turn2_resp = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "When do these releases take place?",
            "provider": "ollama"
        })

        assert turn2_resp.status_code == status.HTTP_200_OK
        # Verify history passed to run_agent contains previous turns
        call_args = mock_adapter.run_agent.call_args[1]
        history_passed = call_args["history"]
        assert len(history_passed) == 2  # user msg 1 + asst msg 1


# --- TEST 5: Refresh Verification (Persisted Data Consistency) ---

def test_refresh_loads_identical_messages_and_citations(client, seeded_db):
    create_resp = client.post("/api/sessions", json={"title": "New Chat", "provider": "ollama"})
    session_id = create_resp.json()["id"]

    mock_result = {
        "content": "Elena Verna stresses that simplifying onboarding should not be treated as a roadmap line item.",
        "sources": [
            {
                "title": "10 growth tactics that never work | Elena Verna",
                "source_url": "https://www.youtube.com/watch?v=elena_123",
                "chunk_id": "chunk_elena_1",
                "score": 20.4
            }
        ],
        "artifact": None,
        "provider_used": "ollama",
        "model_used": "qwen2.5:3b"
    }

    with patch("backend.app.api.chat.get_agent_adapter") as mock_get_adapter:
        mock_adapter = AsyncMock()
        mock_adapter.run_agent.return_value = mock_result
        mock_get_adapter.return_value = mock_adapter

        chat_resp = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "What does Elena Verna say about onboarding?",
            "provider": "ollama"
        })
        assert chat_resp.status_code == status.HTTP_200_OK
        chat_data = chat_resp.json()

    # Simulate page refresh by retrieving session messages
    refresh_resp = client.get(f"/api/sessions/{session_id}/messages")
    assert refresh_resp.status_code == status.HTTP_200_OK
    messages = refresh_resp.json()

    assert len(messages) == 2
    user_msg = messages[0]
    asst_msg = messages[1]

    assert user_msg["role"] == "user"
    assert user_msg["content"] == "What does Elena Verna say about onboarding?"

    assert asst_msg["role"] == "assistant"
    assert asst_msg["content"] == chat_data["content"]
    assert len(asst_msg["sources"]) == 1
    assert asst_msg["sources"][0]["title"] == "10 growth tactics that never work | Elena Verna"
    assert asst_msg["sources"][0]["score"] == 20.4


# --- TEST 6: Simulated Ollama Timeout & Exception Handling ---

def test_simulated_ollama_timeout_rolls_back_orphan_user_message(client, seeded_db):
    create_resp = client.post("/api/sessions", json={"title": "New Chat", "provider": "ollama"})
    session_id = create_resp.json()["id"]

    with patch("backend.app.api.chat.get_agent_adapter") as mock_get_adapter:
        mock_adapter = AsyncMock()
        mock_adapter.run_agent.side_effect = RuntimeError("Connection timed out waiting for Ollama.")
        mock_get_adapter.return_value = mock_adapter

        chat_resp = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "Failing query to test timeout",
            "provider": "ollama"
        })

        assert chat_resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "timed out" in chat_resp.json()["detail"]

    # Verify no orphan user message remains in DB after failure
    check_resp = client.get(f"/api/sessions/{session_id}/messages")
    assert check_resp.status_code == status.HTTP_200_OK
    assert len(check_resp.json()) == 0
