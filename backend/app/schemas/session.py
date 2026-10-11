from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Source Citation Schema ---
class SourceCitation(BaseModel):
    title: str
    source_url: str | None = None
    chunk_id: str | None = None
    score: float | None = None

# --- Message Schemas ---
class MessageCreate(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', 'system', 'tool'")
    content: str = Field(..., description="Message text content")
    sources: list[SourceCitation] = Field(default_factory=list)

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    sources: list[SourceCitation] = Field(default_factory=list)
    created_at: datetime

# --- Session Schemas ---
class SessionCreate(BaseModel):
    title: str = Field("New Chat", description="Session title")
    provider: str = Field("ollama", description="Model provider ('ollama' or 'cloud')")
    model: str = Field("qwen2.5:3b", description="Model identifier")

class SessionUpdate(BaseModel):
    title: str | None = None
    provider: str | None = None
    model: str | None = None

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

# --- Artifact Schemas ---
class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    message_id: str | None = None
    title: str
    artifact_type: str
    content: str
    created_at: datetime

# --- Chat Request/Response Schemas ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: str | None = None
    model: str | None = None

class ChatResponse(BaseModel):
    id: str
    session_id: str
    role: str = "assistant"
    content: str
    sources: list[SourceCitation] = Field(default_factory=list)
    artifact: ArtifactResponse | None = None
    provider_used: str
    model_used: str

# --- Health & Config Schemas ---
class HealthResponse(BaseModel):
    status: str
    database: bool
    ollama: bool
    version: str = "1.0.0"

class ConfigResponse(BaseModel):
    active_provider: str
    active_model: str
    ollama_url: str
    cloud_key_configured: bool
    supported_providers: list[str] = ["ollama", "cloud"]
    sdk_integration: str = "Anthropic Claude Agent SDK (claude-agent-sdk)"
