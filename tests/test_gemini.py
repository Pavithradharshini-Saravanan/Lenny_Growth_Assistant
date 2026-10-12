import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.agent.gemini_agent import GeminiAgentAdapter
from backend.app.agent.dispatcher import get_agent_adapter
from backend.app.agent.base import ConfigurationError
from backend.app.config import settings

client = TestClient(app)


def test_gemini_missing_api_key_raises_configuration_error():
    """Verify selecting Gemini with no API key raises ConfigurationError (zero silent fallback)."""
    with patch("backend.app.config.settings.GEMINI_API_KEY", None):
        adapter = GeminiAgentAdapter(api_key=None)
        with pytest.raises(ConfigurationError) as exc_info:
            adapter._verify_configuration()
        assert "GEMINI_API_KEY" in str(exc_info.value)
        assert "Google Gemini requires the GEMINI_API_KEY" in str(exc_info.value)


def test_dispatcher_returns_gemini_adapter():
    """Verify dispatcher returns GeminiAgentAdapter when requested."""
    adapter = get_agent_adapter(provider="gemini")
    assert isinstance(adapter, GeminiAgentAdapter)
    assert adapter.provider_name == "gemini"

    # Also supports alias 'google'
    adapter_google = get_agent_adapter(provider="google")
    assert isinstance(adapter_google, GeminiAgentAdapter)


def test_chat_endpoint_missing_gemini_key_returns_400():
    """Verify POST /api/chat with provider='gemini' returns HTTP 400 when GEMINI_API_KEY is not set."""
    # Create a fresh session
    sess_res = client.post("/api/sessions", json={"title": "Gemini Test Session", "provider": "gemini"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]


    with patch("backend.app.config.settings.GEMINI_API_KEY", None):
        chat_res = client.post(
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "What is the best PM onboarding strategy?",
                "provider": "gemini"
            }
        )
        assert chat_res.status_code == 400
        data = chat_res.json()
        assert "GEMINI_API_KEY" in data["detail"]

    # Verify no orphan user messages were persisted
    msg_res = client.get(f"/api/sessions/{session_id}/messages")
    assert msg_res.status_code == 200
    assert len(msg_res.json()) == 0


@pytest.mark.anyio
async def test_gemini_agent_tool_calling_mocked():
    """Verify Gemini agent properly calls search_transcripts tool and synthesizes grounded answer."""
    adapter = GeminiAgentAdapter(api_key="mock-gemini-key")

    turn1_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "search_transcripts",
                                "arguments": json.dumps({"query": "Elena Verna onboarding", "top_k": 3})
                            }
                        }
                    ]
                }
            }
        ]
    }

    turn2_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "According to Elena Verna, optimizing onboarding friction is critical for product-led growth."
                }
            }
        ]
    }

    with patch.object(adapter, "_post_chat_completion", side_effect=[turn1_response, turn2_response]) as mock_post:
        result = await adapter.run_agent(prompt="What does Elena Verna say about onboarding?")
        assert result["provider_used"] == "gemini"
        assert "Elena Verna" in result["content"]
        assert mock_post.call_count == 2
        # Check that sources were populated
        assert isinstance(result["sources"], list)


@pytest.mark.anyio
async def test_gemini_agent_ship30_tool_mocked():
    """Verify Gemini agent properly executes run_ship30_skill and attaches markdown artifact."""
    adapter = GeminiAgentAdapter(api_key="mock-gemini-key")

    turn1_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_ship30",
                            "type": "function",
                            "function": {
                                "name": "run_ship30_skill",
                                "arguments": json.dumps({"topic": "Product-Led Growth Onboarding", "audience": "Growth PMs"})
                            }
                        }
                    ]
                }
            }
        ]
    }

    turn2_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Here is the completed Ship 30 for 30 essay on PLG onboarding."
                }
            }
        ]
    }

    with patch.object(adapter, "_post_chat_completion", side_effect=[turn1_response, turn2_response]):
        result = await adapter.run_agent(prompt="Write a Ship 30 essay on PLG onboarding")
        assert result["provider_used"] == "gemini"
        assert result["artifact"] is not None
        assert result["artifact"]["artifact_type"] == "markdown"
        assert "Product-Led Growth Onboarding" in result["artifact"]["title"]


@pytest.mark.anyio
async def test_gemini_agent_rate_limit_error_handling():
    """Verify Gemini agent handles 429 rate limit errors with a clear user message."""
    adapter = GeminiAgentAdapter(api_key="mock-gemini-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit exceeded"

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp

    with pytest.raises(RuntimeError) as exc_info:
        await adapter._post_chat_completion(mock_client, {"messages": []}, max_retries=0)
    assert "rate limit" in str(exc_info.value).lower()
