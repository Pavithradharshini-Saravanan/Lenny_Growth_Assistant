from backend.app.agent.base import BaseAgentAdapter
from backend.app.agent.claude_agent import ClaudeAgentSDKAdapter
from backend.app.agent.ollama_agent import OllamaAgentAdapter
from backend.app.agent.gemini_agent import GeminiAgentAdapter
from backend.app.config import settings

def get_agent_adapter(provider: str | None = None, model: str | None = None) -> BaseAgentAdapter:
    chosen_provider = (provider or settings.PROVIDER_TYPE).lower().strip()
    if chosen_provider == "cloud":
        return ClaudeAgentSDKAdapter(model=model)
    elif chosen_provider == "ollama":
        return OllamaAgentAdapter(model=model)
    elif chosen_provider in ("gemini", "google"):
        return GeminiAgentAdapter(model=model)
    else:
        raise ValueError(
            f"Unsupported provider '{chosen_provider}'. Supported options: 'ollama', 'cloud', 'gemini'."
        )
