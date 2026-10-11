from abc import ABC, abstractmethod
from typing import Any

class ConfigurationError(Exception):
    """Raised when a model provider or agent SDK is misconfigured or missing credentials."""
    pass

class BaseAgentAdapter(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def sdk_name(self) -> str:
        pass

    @abstractmethod
    async def run_agent(
        self,
        prompt: str,
        history: list[dict[str, Any]] | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Execute agentic loop and return response dict containing content, sources, and artifact."""
        pass
