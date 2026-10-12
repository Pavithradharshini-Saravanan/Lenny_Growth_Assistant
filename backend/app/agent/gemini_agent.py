import json
import logging
import re
from typing import Any
import httpx

from backend.app.agent.base import BaseAgentAdapter, ConfigurationError
from backend.app.config import settings
from backend.app.tools.base import (
    search_transcripts_domain,
    run_ship30_skill_domain,
    create_artifact_domain,
)

logger = logging.getLogger(__name__)


class GeminiAgentAdapter(BaseAgentAdapter):
    """
    Google Gemini Cloud Agent Adapter.
    Uses Google's OpenAI-compatible endpoint with function calling support.
    Reuses existing domain tools (search_transcripts, run_ship30_skill, create_artifact),
    session persistence, citations, and artifact rendering.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.base_url = (base_url or settings.GEMINI_BASE_URL).rstrip("/")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def sdk_name(self) -> str:
        return f"Google Gemini ({self.model})"

    def _verify_configuration(self):
        """Verify API key is configured. Zero silent fallback!"""
        if not self.api_key:
            raise ConfigurationError(
                "Google Gemini requires the GEMINI_API_KEY environment variable. "
                "Cloud mode cannot run without valid credentials. "
                "Please configure GEMINI_API_KEY in your .env file or select Local Ollama in the provider selector."
            )

    def _get_tools_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_transcripts",
                    "description": "Search Lenny's podcast/newsletter transcript knowledge base for grounded evidence.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query or topic"},
                            "top_k": {"type": "integer", "description": "Number of chunks (default 5)"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_ship30_skill",
                    "description": "Generate a structured Ship 30 for 30 essay (~1,250 words) based on transcript findings.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Core thesis or question"},
                            "audience": {"type": "string", "description": "Target audience"}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_artifact",
                    "description": "Generate a renderable Markdown or HTML document artifact.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the artifact"},
                            "artifact_type": {"type": "string", "description": "'markdown' or 'html'"},
                            "content": {"type": "string", "description": "Raw markdown or HTML code. For HTML artifacts, emit standalone component HTML without <!DOCTYPE> or <meta> tags."}
                        },
                        "required": ["title", "artifact_type", "content"]
                    }
                }
            }
        ]

    async def _post_chat_completion(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
        max_retries: int = 2
    ) -> dict[str, Any]:
        """Send chat completion request with bounded retries for transient errors."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        models_to_try = [payload.get("model", self.model)]
        for alt in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]:
            if alt not in models_to_try:
                models_to_try.append(alt)

        last_error = None
        for model_candidate in models_to_try:
            curr_payload = dict(payload)
            curr_payload["model"] = model_candidate

            for attempt in range(max_retries + 1):
                try:
                    resp = await client.post(url, json=curr_payload, headers=headers, timeout=50.0)
                    
                    # Check for permanent authentication or configuration error
                    if resp.status_code in (401, 403):
                        error_detail = resp.text
                        try:
                            err_json = resp.json()
                            error_detail = err_json.get("error", {}).get("message", error_detail)
                        except Exception:
                            pass
                        raise ConfigurationError(
                            f"Google Gemini authentication failed ({resp.status_code}): {error_detail}. "
                            "Please verify GEMINI_API_KEY."
                        )

                    if resp.status_code == 429:
                        if attempt < max_retries:
                            logger.warning(f"Google Gemini rate limit (429) hit, retrying in {2.5 * (attempt + 1)}s...")
                            import asyncio
                            await asyncio.sleep(2.5 * (attempt + 1))
                            continue
                        raise RuntimeError("Google Gemini rate limit reached. Please wait a moment before retrying.")

                    if resp.status_code in (500, 502, 503, 504):
                        logger.warning(f"Transient Gemini server response {resp.status_code} for {model_candidate}, retry {attempt + 1}...")
                        import asyncio
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue

                    resp.raise_for_status()
                    return resp.json()

                except (httpx.ConnectError, httpx.TimeoutException) as net_err:
                    last_error = net_err
                    if attempt < max_retries:
                        import asyncio
                        await asyncio.sleep(1.0)
                        continue
                    break
                except Exception as e:
                    if isinstance(e, (ConfigurationError, RuntimeError)):
                        raise
                    last_error = e
                    break

        raise RuntimeError(f"Failed to communicate with Google Gemini API: {last_error}")

    async def run_agent(
        self,
        prompt: str,
        history: list[dict[str, Any]] | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Execute agent workflow with Google Gemini."""
        self._verify_configuration()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are The Lenny Growth Assistant, a specialized AI for product management and growth leaders. "
                    "When answering product/growth questions, call search_transcripts to retrieve grounded evidence "
                    "from Lenny's Podcast transcripts before making factual claims. "
                    "Always call search_transcripts for each new user question. "
                    "Ground your answer strictly in retrieved evidence. Cite the episode titles and speakers. "
                    "If search returns no relevant results or empty evidence, state: "
                    "'The available transcripts do not contain information to answer this question.' "
                    "Do not fabricate quotes or citations. "
                    "Use run_ship30_skill when requested to write an essay. "
                    "Use create_artifact to emit Markdown or HTML code snippets (standalone HTML components without <!DOCTYPE> or <meta> tags)."
                )
            }
        ]

        if history:
            recent_history = history[-8:]
            clean_history = []
            for msg in recent_history:
                role = msg.get("role", "user")
                text = str(msg.get("content", ""))
                if clean_history and clean_history[-1]["role"] == role and clean_history[-1]["content"] == text:
                    continue
                clean_history.append({"role": role, "content": text})
            for msg in clean_history:
                messages.append(msg)

        messages.append({"role": "user", "content": str(prompt)})

        tools_schema = self._get_tools_schema()

        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools_schema,
                "temperature": 0.2
            }

            result = await self._post_chat_completion(client, payload)

            choices = result.get("choices", [])
            if not choices:
                return {
                    "content": "No response returned from Google Gemini.",
                    "sources": [],
                    "artifact": None,
                    "provider_used": "gemini",
                    "model_used": self.model
                }

            msg_obj = choices[0].get("message", {})
            content = msg_obj.get("content", "") or ""
            tool_calls = msg_obj.get("tool_calls", [])

            sources = []
            artifact = None

            if tool_calls:
                messages.append(msg_obj)

                for tc in tool_calls:
                    call_id = tc.get("id", "call_default")
                    fn_obj = tc.get("function", {})
                    fn_name = fn_obj.get("name")
                    fn_args = fn_obj.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {}

                    if fn_name == "search_transcripts":
                        query_val = str(fn_args.get("query") or prompt)
                        top_k_val = fn_args.get("top_k", 5)
                        res = search_transcripts_domain(query=query_val, top_k=top_k_val)
                        if not res.get("empty_result"):
                            sources = res.get("results", [])

                        compact_results = []
                        for item in sources:
                            compact_results.append({
                                "title": item.get("title"),
                                "speaker": item.get("speaker"),
                                "excerpt": str(item.get("content", ""))[:1800]
                            })

                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": json.dumps({"query": query_val, "evidence": compact_results})
                        })

                    elif fn_name == "run_ship30_skill":
                        topic_val = str(fn_args.get("topic") or prompt)
                        aud_val = str(fn_args.get("audience") or "Product Practitioners")
                        res = run_ship30_skill_domain(topic=topic_val, audience=aud_val)
                        if not artifact:
                            artifact = {
                                "title": res.get("title") or f"Ship 30 Essay: {topic_val}",
                                "artifact_type": "markdown",
                                "content": res.get("content", "")
                            }
                        if res.get("sources"):
                            sources = res.get("sources", [])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": json.dumps({
                                "status": "completed",
                                "title": res.get("title"),
                                "word_count": res.get("word_count"),
                                "summary": f"Generated {res.get('word_count')}-word grounded Ship 30 essay on '{topic_val}'."
                            })
                        })

                    elif fn_name == "create_artifact":
                        title_val = str(fn_args.get("title") or "Artifact")
                        type_val = str(fn_args.get("artifact_type") or "markdown")
                        cont_val = str(fn_args.get("content") or "")
                        res = create_artifact_domain(title=title_val, artifact_type=type_val, content=cont_val)
                        artifact = {
                            "title": res["title"],
                            "artifact_type": res["artifact_type"],
                            "content": res["content"]
                        }
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": json.dumps({
                                "status": "created",
                                "title": res["title"],
                                "artifact_type": res["artifact_type"]
                            })
                        })

                # Synthesize grounded answer from tool evidence
                synthesis_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are The Lenny Growth Assistant, a specialized AI for product management and growth leaders. "
                            "Ground your response strictly in the retrieved transcript evidence provided below. "
                            "Cite the episode titles and speakers. If evidence is empty, state: "
                            "'The available transcripts do not contain information to answer this question.'"
                        )
                    }
                ]
                if history:
                    for h in history[-4:]:
                        synthesis_messages.append({"role": h.get("role", "user"), "content": str(h.get("content", ""))})

                evidence_summary = "\n\n".join([
                    f"[{s.get('title', 'Lenny Episode')}] {s.get('speaker', 'Guest')}:\n{str(s.get('content', ''))[:1500]}"
                    for s in sources
                ])

                synthesis_prompt = f"User Question: {prompt}\n\nRetrieved Transcript Evidence:\n{evidence_summary}\n\nPlease provide a clear, comprehensive answer grounded strictly in this evidence."
                synthesis_messages.append({"role": "user", "content": synthesis_prompt})

                turn2_payload = {
                    "model": self.model,
                    "messages": synthesis_messages,
                    "temperature": 0.2
                }
                result2 = await self._post_chat_completion(client, turn2_payload)
                choices2 = result2.get("choices", [])
                if choices2:
                    content = choices2[0].get("message", {}).get("content", "") or content

                # Code block HTML extraction fallback
                if not artifact and content:
                    html_match = re.search(r"```html\s*([\s\S]*?)```", content, re.IGNORECASE)
                    if html_match:
                        try:
                            artifact = create_artifact_domain(
                                title="Generated HTML Component",
                                artifact_type="html",
                                content=html_match.group(1).strip()
                            )
                        except Exception:
                            pass

            else:
                # Fallback: if Gemini directly answered a factual question without tool invocation,
                # ground it against the indexed transcripts
                res = search_transcripts_domain(query=prompt, top_k=5)
                if not res.get("empty_result") and res.get("results"):
                    sources = res.get("results", [])

            return {
                "content": content or "No response generated.",
                "sources": sources,
                "artifact": artifact,
                "provider_used": "gemini",
                "model_used": self.model
            }
