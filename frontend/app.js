// Frontend Application Logic for The Lenny Growth Assistant
const API_BASE = '/api';
let currentSessionId = null;
let currentProvider = 'ollama';

document.addEventListener('DOMContentLoaded', async () => {
    await initApp();
    setupEventListeners();
});

async function initApp() {
    await checkConfig();
    await checkHealth();
    await loadSessions();
}

async function checkConfig() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        if (res.ok) {
            const data = await res.json();
            currentProvider = data.active_provider;
            document.getElementById('providerSelect').value = currentProvider;
        }
    } catch (e) {
        console.error('Config fetch failed:', e);
    }
}

async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const badge = document.getElementById('providerStatusBadge');
        if (res.ok) {
            const data = await res.json();
            if (data.status === 'ok') {
                badge.textContent = 'Healthy';
                badge.className = 'status-badge badge-active';
            } else {
                badge.textContent = 'Degraded';
                badge.className = 'status-badge badge-error';
            }
        }
    } catch (e) {
        const badge = document.getElementById('providerStatusBadge');
        badge.textContent = 'Offline';
        badge.className = 'status-badge badge-error';
    }
}

function setupEventListeners() {
    document.getElementById('btnNewChat').addEventListener('click', createNewSession);
    document.getElementById('providerSelect').addEventListener('change', handleProviderChange);
    document.getElementById('chatForm').addEventListener('submit', handleChatSubmit);
}

async function loadSessions() {
    try {
        const res = await fetch(`${API_BASE}/sessions`);
        if (res.ok) {
            const sessions = await res.json();
            renderSessionList(sessions);
            if (sessions.length > 0 && !currentSessionId) {
                switchSession(sessions[0].id);
            }
        }
    } catch (e) {
        console.error('Failed to load sessions:', e);
    }
}

function renderSessionList(sessions) {
    const listEl = document.getElementById('sessionList');
    listEl.innerHTML = '';
    sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = `session-item ${s.id === currentSessionId ? 'active' : ''}`;
        item.onclick = () => switchSession(s.id);

        item.innerHTML = `
            <span class="session-title">${escapeHtml(s.title)}</span>
            <button class="session-delete" onclick="deleteSession(event, '${s.id}')">✕</button>
        `;
        listEl.appendChild(item);
    });
}

async function createNewSession() {
    try {
        const res = await fetch(`${API_BASE}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat', provider: currentProvider })
        });
        if (res.ok) {
            const newSession = await res.json();
            currentSessionId = newSession.id;
            await loadSessions();
            switchSession(currentSessionId);
        }
    } catch (e) {
        console.error('Failed to create session:', e);
    }
}

async function switchSession(sessionId) {
    currentSessionId = sessionId;
    await loadSessions(); // Update active highlights

    // Clear chat messages container
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';
    hideAlert();
    closeArtifactPanel();

    try {
        const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
        if (res.ok) {
            const messages = await res.json();
            if (messages.length === 0) {
                renderEmptyState();
            } else {
                messages.forEach(m => renderMessage(m.role, m.content, m.sources));
            }
        }

        // Check for session artifacts and render if present
        const artRes = await fetch(`${API_BASE}/sessions/${sessionId}/artifacts`);
        if (artRes.ok) {
            const artifacts = await artRes.json();
            if (artifacts && artifacts.length > 0) {
                openArtifactViewer(artifacts[artifacts.length - 1]);
            }
        }
    } catch (e) {
        console.error('Failed to fetch session messages or artifacts:', e);
    }
}

async function deleteSession(event, sessionId) {
    event.stopPropagation();
    if (!confirm('Delete this session?')) return;
    try {
        await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
        if (sessionId === currentSessionId) {
            currentSessionId = null;
        }
        await loadSessions();
    } catch (e) {
        console.error('Delete failed:', e);
    }
}

function handleProviderChange(e) {
    currentProvider = e.target.value;
    hideAlert();
}

let isSubmitting = false;

async function handleChatSubmit(e) {
    e.preventDefault();
    if (isSubmitting) return;

    const input = document.getElementById('userInput');
    const submitBtn = document.querySelector('#chatForm button[type="submit"]');
    const text = input.value.trim();
    if (!text) return;

    isSubmitting = true;
    if (submitBtn) submitBtn.disabled = true;
    input.disabled = true;

    if (!currentSessionId) {
        await createNewSession();
    }

    input.value = '';
    hideAlert();

    // Render User Message immediately with temp ID
    hideEmptyState();
    const userMsgId = 'user-msg-' + Date.now();
    renderMessage('user', text, [], userMsgId);

    // Render loading indicator
    const loadingId = renderLoadingMessage();

    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: text,
                provider: currentProvider
            })
        });

        removeMessage(loadingId);

        if (!res.ok) {
            const errData = await res.json();
            // Backend rolled back the user message, remove it from UI DOM as well
            removeMessage(userMsgId);
            input.value = text; // Restore text for user convenience
            showAlert(errData.detail || 'An error occurred processing request.');
            return;
        }

        const data = await res.json();
        renderMessage('assistant', data.content, data.sources);

        if (data.artifact) {
            openArtifactViewer(data.artifact);
        }

        await loadSessions();
    } catch (e) {
        removeMessage(loadingId);
        removeMessage(userMsgId);
        input.value = text; // Restore text for retry
        showAlert('Network error or server unavailable.');
    } finally {
        isSubmitting = false;
        if (submitBtn) submitBtn.disabled = false;
        input.disabled = false;
        input.focus();
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('userInput').value = promptText;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

function renderEmptyState() {
    const container = document.getElementById('chatMessages');
    container.innerHTML = `
        <div id="emptyState" class="empty-state">
            <div class="empty-icon">💡</div>
            <h2>Ask Lenny Growth Assistant</h2>
            <p>Get transcript-grounded insights, draft Ship 30 for 30 essays, or build interactive growth artifacts.</p>
            <div class="quick-prompts">
                <button class="quick-card" onclick="sendQuickPrompt('How do top PLG companies optimize user onboarding friction?')">
                    <strong>⚡ PLG Onboarding</strong>
                    <span>How do top PLG companies optimize onboarding?</span>
                </button>
                <button class="quick-card" onclick="sendQuickPrompt('Write a Ship 30 for 30 essay on product-market fit metrics.')">
                    <strong>✍️ Ship 30 Essay</strong>
                    <span>Write an essay on PMF metrics</span>
                </button>
                <button class="quick-card" onclick="sendQuickPrompt('Create an HTML dashboard component for tracking North Star metrics.')">
                    <strong>🎨 HTML Component</strong>
                    <span>Create a North Star metrics dashboard visual</span>
                </button>
            </div>
        </div>
    `;
}

function hideEmptyState() {
    const empty = document.getElementById('emptyState');
    if (empty) empty.remove();
}

function renderMessage(role, content, sources = [], elemId = null) {
    const container = document.getElementById('chatMessages');
    const msgCard = document.createElement('div');
    if (elemId) msgCard.id = elemId;
    msgCard.className = `message-card ${role === 'user' ? 'message-user' : 'message-assistant'}`;

    let html = `<div>${escapeHtml(content).replace(/\n/g, '<br>')}</div>`;

    if (sources && sources.length > 0) {
        html += `<div class="source-badges">`;
        sources.forEach(s => {
            html += `<span class="source-badge">📌 ${escapeHtml(s.title)}</span>`;
        });
        html += `</div>`;
    }

    msgCard.innerHTML = html;
    container.appendChild(msgCard);
    container.scrollTop = container.scrollHeight;
}

function renderLoadingMessage() {
    const container = document.getElementById('chatMessages');
    const id = 'msg-' + Date.now();
    const loadingCard = document.createElement('div');
    loadingCard.id = id;
    loadingCard.className = 'message-card message-assistant';
    loadingCard.innerHTML = `<div><em>Thinking...</em></div>`;
    container.appendChild(loadingCard);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function renderMarkdownToHtml(md) {
    if (!md) return '';
    let text = escapeHtml(md);

    // Headers
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Blockquotes
    text = text.replace(/^\&gt; (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bold & Italics
    text = text.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Unordered lists
    text = text.replace(/^\- (.*$)/gim, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Paragraphs
    const paragraphs = text.split(/\n\s*\n/);
    return paragraphs.map(p => {
        p = p.trim();
        if (p.startsWith('<h') || p.startsWith('<blockquote') || p.startsWith('<ul') || p.startsWith('<li')) {
            return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('\n');
}

function openArtifactViewer(artifact) {
    if (!artifact) return;
    const panel = document.getElementById('artifactPanel');
    panel.classList.remove('hidden');

    document.getElementById('artifactTitle').textContent = artifact.title || 'Artifact';
    document.getElementById('artifactBadge').textContent = (artifact.artifact_type || 'markdown').toUpperCase();

    const rawCode = document.getElementById('artifactRawCode');
    rawCode.textContent = artifact.content || '';

    const iframe = document.getElementById('artifactIframe');
    if (artifact.artifact_type === 'html') {
        iframe.srcdoc = artifact.content || '';
    } else {
        const rendered = renderMarkdownToHtml(artifact.content || '');
        iframe.srcdoc = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 24px 32px;
            line-height: 1.7;
            color: #1e293b;
            background: #ffffff;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 { font-size: 1.75rem; font-weight: 700; color: #0f172a; margin-bottom: 1rem; line-height: 1.3; }
        h2 { font-size: 1.35rem; font-weight: 600; color: #1e293b; margin-top: 1.8rem; margin-bottom: 0.8rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }
        h3 { font-size: 1.15rem; font-weight: 600; color: #334155; margin-top: 1.2rem; }
        p { margin-bottom: 1rem; }
        blockquote {
            border-left: 4px solid #6366f1;
            padding: 8px 16px;
            margin: 16px 0;
            background: #f8fafc;
            color: #475569;
            font-style: italic;
        }
        ul, ol { padding-left: 24px; margin-bottom: 1rem; }
        li { margin-bottom: 6px; }
        strong { font-weight: 600; color: #0f172a; }
        code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
        a { color: #6366f1; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    ${rendered}
</body>
</html>`;
    }
}

function copyArtifactCode() {
    const rawCode = document.getElementById('artifactRawCode').textContent;
    navigator.clipboard.writeText(rawCode).then(() => {
        const btn = document.getElementById('btnCopyCode');
        if (btn) {
            btn.textContent = '✓ Copied!';
            setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
        }
    }).catch(err => {
        console.error('Copy failed:', err);
    });
}

function closeArtifactPanel() {
    document.getElementById('artifactPanel').classList.add('hidden');
}

function switchArtifactTab(tab) {
    const tabPrev = document.getElementById('tabPreview');
    const tabCode = document.getElementById('tabCode');
    const viewPrev = document.getElementById('artifactPreviewContainer');
    const viewCode = document.getElementById('artifactCodeContainer');

    if (tab === 'preview') {
        tabPrev.classList.add('active');
        tabCode.classList.remove('active');
        viewPrev.classList.remove('hidden');
        viewCode.classList.add('hidden');
    } else {
        tabCode.classList.add('active');
        tabPrev.classList.remove('active');
        viewCode.classList.remove('hidden');
        viewPrev.classList.add('hidden');
    }
}

function showAlert(msg) {
    const banner = document.getElementById('alertBanner');
    banner.textContent = msg;
    banner.classList.remove('hidden');
}

function hideAlert() {
    const banner = document.getElementById('alertBanner');
    banner.classList.add('hidden');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
