import pytest
from backend.app.agent.dispatcher import get_agent_adapter
from backend.app.agent.base import ConfigurationError
from backend.app.agent.claude_agent import ClaudeAgentSDKAdapter
from backend.app.agent.ollama_agent import OllamaAgentAdapter

def test_agent_dispatcher_instantiation():
    ollama_adapter = get_agent_adapter(provider="ollama")
    assert isinstance(ollama_adapter, OllamaAgentAdapter)
    assert ollama_adapter.provider_name == "ollama"

    cloud_adapter = get_agent_adapter(provider="cloud")
    assert isinstance(cloud_adapter, ClaudeAgentSDKAdapter)
    assert cloud_adapter.provider_name == "cloud"

def test_missing_cloud_key_raises_error(client):
    # Ensure no cloud API key is set for test
    adapter = ClaudeAgentSDKAdapter(api_key=None)
    with pytest.raises(ConfigurationError) as exc_info:
        adapter._verify_configuration()
    assert "Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY" in str(exc_info.value)

def test_chat_endpoint_missing_cloud_key_returns_400(client):
    # Create a session configured for Cloud provider
    s_res = client.post("/api/sessions", json={"title": "Cloud Chat", "provider": "cloud"}).json()
    session_id = s_res["id"]

    # Send message with provider="cloud" when no key is set
    chat_res = client.post("/api/chat", json={"session_id": session_id, "message": "Test Cloud", "provider": "cloud"})
    
    # Must return HTTP 400 Bad Request with explicit error message (NO SILENT FALLBACK)
    assert chat_res.status_code == 400
    err_detail = chat_res.json()["detail"]
    assert "Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY" in err_detail

@pytest.mark.anyio
async def test_ollama_agent_tool_call_and_re_search_regression():
    import json
    from unittest.mock import patch, MagicMock

    adapter = OllamaAgentAdapter(base_url="http://mock-ollama:11434", model="qwen2.5:3b")

    alive_resp = MagicMock()
    alive_resp.status = 200

    turn1_data = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_transcripts",
                        "arguments": {"query": "Shreyas Doshi"}
                    }
                }
            ]
        }
    }
    turn1_resp = MagicMock()
    turn1_resp.read.return_value = json.dumps(turn1_data).encode("utf-8")
    turn1_resp.__enter__.return_value = turn1_resp

    turn2_data = {
        "message": {
            "role": "assistant",
            "content": "According to Shreyas Doshi, most execution problems are actually strategy problems.\n```html\n<div>Summary</div>\n```"
        }
    }
    turn2_resp = MagicMock()
    turn2_resp.read.return_value = json.dumps(turn2_data).encode("utf-8")
    turn2_resp.__enter__.return_value = turn2_resp

    with patch("urllib.request.urlopen", side_effect=[alive_resp, turn1_resp, turn2_resp]):
        res = await adapter.run_agent(prompt="What does Shreyas Doshi say about execution?")
        assert res is not None
        assert "Shreyas Doshi" in res["content"]
        assert res["provider_used"] == "ollama"
        assert res["artifact"] is not None
        assert res["artifact"]["artifact_type"] == "html"

@pytest.mark.anyio
async def test_ollama_agent_plain_text_no_re_name_error():
    import json
    from unittest.mock import patch, MagicMock

    adapter = OllamaAgentAdapter(base_url="http://mock-ollama:11434", model="qwen2.5:3b")

    alive_resp = MagicMock()
    alive_resp.status = 200

    turn1_data = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_transcripts",
                        "arguments": {"query": "Shreyas Doshi"}
                    }
                }
            ]
        }
    }
    turn1_resp = MagicMock()
    turn1_resp.read.return_value = json.dumps(turn1_data).encode("utf-8")
    turn1_resp.__enter__.return_value = turn1_resp

    turn2_data = {
        "message": {
            "role": "assistant",
            "content": "Shreyas Doshi explains that execution problems are often strategy problems."
        }
    }
    turn2_resp = MagicMock()
    turn2_resp.read.return_value = json.dumps(turn2_data).encode("utf-8")
    turn2_resp.__enter__.return_value = turn2_resp

    with patch("urllib.request.urlopen", side_effect=[alive_resp, turn1_resp, turn2_resp]):
        res = await adapter.run_agent(prompt="What did Shreyas say?")
        assert res is not None
        assert "Shreyas Doshi" in res["content"]

