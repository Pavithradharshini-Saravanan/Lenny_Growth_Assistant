import pytest

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "ollama" in data

def test_config_endpoint(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["active_provider"] in ["ollama", "cloud", "gemini"]
    assert "sdk_integration" in data
    assert "supported_providers" in data

def test_session_lifecycle(client):
    # 1. Create Session
    create_res = client.post("/api/sessions", json={"title": "Test Session", "provider": "ollama"})
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test Session"

    # 2. Get Session
    get_res = client.get(f"/api/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 3. List Sessions
    list_res = client.get("/api/sessions")
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert any(s["id"] == session_id for s in sessions)

    # 4. Update Session Title
    patch_res = client.patch(f"/api/sessions/{session_id}", json={"title": "Updated Session Title"})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Session Title"

    # 5. Delete Session
    del_res = client.delete(f"/api/sessions/{session_id}")
    assert del_res.status_code == 204

    # 6. Verify Deleted
    get_deleted = client.get(f"/api/sessions/{session_id}")
    assert get_deleted.status_code == 404

def test_session_isolation(client, monkeypatch):
    async def mock_run_agent(self, prompt, history=None, session_id=None):
        return {
            "content": f"Echo: {prompt}",
            "sources": [],
            "provider_used": "ollama",
            "model_used": "qwen2.5:3b"
        }
    from backend.app.agent.ollama_agent import OllamaAgentAdapter
    monkeypatch.setattr(OllamaAgentAdapter, "run_agent", mock_run_agent)

    # Create Session A
    s_a = client.post("/api/sessions", json={"title": "Session A"}).json()
    session_a_id = s_a["id"]

    # Create Session B
    s_b = client.post("/api/sessions", json={"title": "Session B"}).json()
    session_b_id = s_b["id"]

    # Send message to Session A
    res = client.post("/api/chat", json={"session_id": session_a_id, "message": "Hello Session A"})
    assert res.status_code == 200

    # Check messages in Session A
    msgs_a = client.get(f"/api/sessions/{session_a_id}/messages").json()
    assert len(msgs_a) > 0
    assert any("Session A" in m["content"] for m in msgs_a if m["role"] == "user")

    # Check messages in Session B - MUST BE EMPTY (Session Isolation)
    msgs_b = client.get(f"/api/sessions/{session_b_id}/messages").json()
    assert len(msgs_b) == 0

def test_chat_title_auto_update_no_name_error(client, monkeypatch):
    """Verify that posting to chat on default 'New Chat' session updates title without SessionUpdate NameError."""
    # Mock Ollama adapter to avoid needing external server for unit test
    async def mock_run_agent(*args, **kwargs):
        return {
            "content": "Mocked response",
            "sources": [],
            "provider_used": "ollama",
            "model_used": "qwen2.5:3b"
        }
    from backend.app.agent.ollama_agent import OllamaAgentAdapter
    monkeypatch.setattr(OllamaAgentAdapter, "run_agent", mock_run_agent)

    s_res = client.post("/api/sessions", json={"title": "New Chat", "provider": "ollama"}).json()
    session_id = s_res["id"]

    res = client.post("/api/chat", json={"session_id": session_id, "message": "What did Brian Chesky say about product marketing?"})
    assert res.status_code == 200
    
    # Verify title was updated
    updated_session = client.get(f"/api/sessions/{session_id}").json()
    assert updated_session["title"].startswith("What did Brian Chesky say")

def test_chat_error_cleanup_no_duplicate_orphan_messages(client, monkeypatch):
    """Verify that if agent execution fails, orphan user message is cleaned up from DB."""
    async def mock_run_agent_error(*args, **kwargs):
        raise RuntimeError("Simulated Ollama error")
    
    from backend.app.agent.ollama_agent import OllamaAgentAdapter
    monkeypatch.setattr(OllamaAgentAdapter, "run_agent", mock_run_agent_error)

    s_res = client.post("/api/sessions", json={"title": "Error Cleanup Session", "provider": "ollama"}).json()
    session_id = s_res["id"]

    # First attempt fails
    res1 = client.post("/api/chat", json={"session_id": session_id, "message": "Failed attempt"})
    assert res1.status_code == 500

    # Check messages in session - MUST BE EMPTY because user message was cleaned up
    msgs = client.get(f"/api/sessions/{session_id}/messages").json()
    assert len(msgs) == 0

def test_existing_session_multi_turn_history(client, monkeypatch):
    """Verify that in an existing session with prior history, subsequent questions execute properly."""
    call_count = 0
    async def mock_multi_turn_agent(self, prompt, history=None, session_id=None):
        nonlocal call_count
        call_count += 1
        return {
            "content": f"Answer to turn {call_count}: {prompt}",
            "sources": [{"title": "Brian Chesky's new playbook", "source_url": "http://test", "chunk_id": "c1", "score": 3.0}],
            "provider_used": "ollama",
            "model_used": "qwen2.5:3b"
        }
    from backend.app.agent.ollama_agent import OllamaAgentAdapter
    monkeypatch.setattr(OllamaAgentAdapter, "run_agent", mock_multi_turn_agent)

    # 1. Create Session
    s_res = client.post("/api/sessions", json={"title": "Multi Turn Session", "provider": "ollama"}).json()
    session_id = s_res["id"]

    # 2. Turn 1
    t1_res = client.post("/api/chat", json={"session_id": session_id, "message": "First question"})
    assert t1_res.status_code == 200
    assert len(t1_res.json()["sources"]) == 1

    # 3. Turn 2 in the same existing session
    t2_res = client.post("/api/chat", json={"session_id": session_id, "message": "Second question"})
    assert t2_res.status_code == 200
    assert len(t2_res.json()["sources"]) == 1

    # 4. Turn 3 in the same existing session
    t3_res = client.post("/api/chat", json={"session_id": session_id, "message": "Third question"})
    assert t3_res.status_code == 200

    # 5. Verify total stored messages on refresh/reload
    messages = client.get(f"/api/sessions/{session_id}/messages").json()
    assert len(messages) == 6  # 3 user messages + 3 assistant messages
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "user"
    assert messages[3]["role"] == "assistant"
    assert messages[4]["role"] == "user"
    assert messages[5]["role"] == "assistant"

def test_existing_session_repeated_questions(client, monkeypatch):
    """Verify that asking repeated identical questions in an existing session preserves message order and sources."""
    async def mock_agent(self, prompt, history=None, session_id=None):
        return {
            "content": f"Grounded response for: {prompt}",
            "sources": [{"title": "Brian Chesky's new playbook", "source_url": "http://test", "chunk_id": "c1", "score": 3.5}],
            "provider_used": "ollama",
            "model_used": "qwen2.5:3b"
        }
    from backend.app.agent.ollama_agent import OllamaAgentAdapter
    monkeypatch.setattr(OllamaAgentAdapter, "run_agent", mock_agent)

    s_res = client.post("/api/sessions", json={"title": "Repeated Query Session", "provider": "ollama"}).json()
    session_id = s_res["id"]

    # Send identical query twice
    q = "What did Brian Chesky say about product marketing?"
    r1 = client.post("/api/chat", json={"session_id": session_id, "message": q})
    assert r1.status_code == 200
    assert len(r1.json()["sources"]) == 1

    r2 = client.post("/api/chat", json={"session_id": session_id, "message": q})
    assert r2.status_code == 200
    assert len(r2.json()["sources"]) == 1

    # Reload session history
    messages = client.get(f"/api/sessions/{session_id}/messages").json()
    assert len(messages) == 4
    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant"]

def test_session_provider_update_and_persistence(client):
    # 1. Create session with 'ollama'
    s_res = client.post("/api/sessions", json={"title": "Provider Switching Test", "provider": "ollama"}).json()
    session_id = s_res["id"]
    assert s_res["provider"] == "ollama"

    # 2. Update session provider to 'cloud'
    patch_res = client.patch(f"/api/sessions/{session_id}", json={"provider": "cloud"})
    assert patch_res.status_code == 200
    assert patch_res.json()["provider"] == "cloud"

    # 3. Retrieve session and confirm provider is persisted as 'cloud'
    get_res = client.get(f"/api/sessions/{session_id}").json()
    assert get_res["provider"] == "cloud"

def test_frontend_assets_contain_keyboard_listener_and_theme():
    import os
    app_js = open("frontend/app.js", encoding="utf-8").read()
    styles_css = open("frontend/styles.css", encoding="utf-8").read()
    index_html = open("frontend/index.html", encoding="utf-8").read()

    # Verify Enter-to-send keydown listener
    assert "e.key === 'Enter'" in app_js
    assert "!e.shiftKey" in app_js
    assert "e.preventDefault()" in app_js
    assert "isSubmitting" in app_js

    # Verify session provider sync in app.js
    assert "sessionsCache" in app_js
    assert "updateProviderStatus" in app_js

    # Verify red-and-black product theme tokens in styles.css
    assert "--bg-canvas: #090A0E" in styles_css
    assert "--accent-red-primary: #DC2626" in styles_css
    assert "prefers-reduced-motion" in styles_css

def test_frontend_message_formatting_cleans_markdown_asterisks():
    """Verify that frontend/app.js formats **bold** into <strong> and cleans raw markdown asterisks."""
    app_js = open("frontend/app.js", encoding="utf-8").read()
    assert "function formatMessageContent" in app_js
    assert "formatted.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')" in app_js
    assert "formatted.replace(/\\*\\*/g, '')" in app_js
    assert "formatMessageContent(content)" in app_js

def test_frontend_scrollbar_hidden_in_chat():
    """Verify that frontend/styles.css hides scrollbars across Firefox, IE/Edge, and WebKit/Blink for chat elements."""
    styles_css = open("frontend/styles.css", encoding="utf-8").read()
    assert "scrollbar-width: none" in styles_css
    assert "-ms-overflow-style: none" in styles_css
    assert ".chat-messages::-webkit-scrollbar" in styles_css
    assert ".session-list::-webkit-scrollbar" in styles_css
    assert "display: none" in styles_css
