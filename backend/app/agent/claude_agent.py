import os
from typing import Any
from backend.app.agent.base import BaseAgentAdapter, ConfigurationError
from backend.app.config import settings

class ClaudeAgentSDKAdapter(BaseAgentAdapter):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.CLOUD_MODEL

    @property
    def provider_name(self) -> str:
        return "cloud"

    @property
    def sdk_name(self) -> str:
        return "Anthropic Claude Agent SDK (claude-agent-sdk)"

    def _verify_configuration(self):
        if not self.api_key:
            raise ConfigurationError(
                "Anthropic Claude Agent SDK requires ANTHROPIC_API_KEY environment variable. "
                "Cloud mode cannot be run without credentials. "
                "Please configure ANTHROPIC_API_KEY in .env or switch provider to Local Ollama."
            )

    async def run_agent(
        self,
        prompt: str,
        history: list[dict[str, Any]] | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        # Explicit check - zero silent fallback!
        self._verify_configuration()

        try:
            # Dynamically import claude_agent_sdk when credentials exist
            from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool

            # Register shared domain tools via SDK @tool decorator
            @tool("search_transcripts", "Search Lenny's podcast/newsletter transcripts", {"query": str, "top_k": int})
            async def search_tool(args: dict[str, Any]) -> dict[str, Any]:
                from backend.app.tools.base import search_transcripts_domain
                return search_transcripts_domain(args.get("query", ""), args.get("top_k", 5))

            @tool("run_ship30_skill", "Generate a Ship 30 for 30 essay", {"topic": str, "audience": str})
            async def ship30_tool(args: dict[str, Any]) -> dict[str, Any]:
                from backend.app.tools.base import run_ship30_skill_domain
                return run_ship30_skill_domain(args.get("topic", ""), args.get("audience", ""))

            @tool("create_artifact", "Create a Markdown or HTML artifact", {"title": str, "artifact_type": str, "content": str})
            async def artifact_tool(args: dict[str, Any]) -> dict[str, Any]:
                from backend.app.tools.base import create_artifact_domain
                return create_artifact_domain(args["title"], args["artifact_type"], args["content"])

            options = ClaudeAgentOptions(
                model=self.model,
                system_prompt=(
                    "You are The Lenny Growth Assistant, a specialized AI for product and growth leaders. "
                    "Use search_transcripts to find grounded evidence from Lenny's Podcast transcripts before answering factual claims. "
                    "If retrieved evidence is empty or does not support an answer, explicitly state that the transcripts do not support an answer. "
                    "Use run_ship30_skill when requested to write an essay. "
                    "Use create_artifact to generate Markdown or HTML snippets."
                )
            )

            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                response_text = ""
                sources = []
                artifact = None

                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        for block in message.content:
                            if hasattr(block, "text"):
                                response_text += block.text

                return {
                    "content": response_text or "No response generated.",
                    "sources": sources,
                    "artifact": artifact,
                    "provider_used": "cloud",
                    "model_used": self.model
                }
        except ImportError:
            raise ConfigurationError("Package 'claude-agent-sdk' is not installed in the environment.")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise e
            raise RuntimeError(f"Claude Agent SDK execution failed: {str(e)}")
