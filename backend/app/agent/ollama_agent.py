import json
import re
import urllib.request
import urllib.error
from typing import Any
from backend.app.agent.base import BaseAgentAdapter, ConfigurationError
from backend.app.config import settings
from backend.app.tools.base import (
    search_transcripts_domain,
    run_ship30_skill_domain,
    create_artifact_domain,
)

class OllamaAgentAdapter(BaseAgentAdapter):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def sdk_name(self) -> str:
        return "Local Ollama Agent Adapter"

    def _check_ollama_alive(self) -> bool:
        try:
            req = urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3)
            return req.status == 200
        except Exception:
            return False

    async def run_agent(
        self,
        prompt: str,
        history: list[dict[str, Any]] | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        if not self._check_ollama_alive():
            raise ConfigurationError(
                f"Local Ollama service is not reachable at {self.base_url}. "
                "Please verify that Ollama is running (`ollama serve`)."
            )

        tools_schema = [
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
                    "description": "Generate a structured Ship 30 for 30 essay based on transcript findings.",
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
                            "content": {"type": "string", "description": "Raw markdown or HTML code"}
                        },
                        "required": ["title", "artifact_type", "content"]
                    }
                }
            }
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are The Lenny Growth Assistant, a specialized AI for product management and growth leaders. "
                    "When answering product/growth questions, call search_transcripts to retrieve evidence. "
                    "Always call search_transcripts to check for evidence for each new user question. "
                    "Ground your answer strictly in retrieved evidence. Cite the episode titles and speakers. "
                    "If search returns no relevant results or empty evidence, state: 'The available transcripts do not contain information to answer this question.' Do not fabricate quotes or citations. "
                    "Use run_ship30_skill for essay requests, and create_artifact to emit Markdown or HTML code snippets."
                )
            }
        ]

        if history:
            # Use a sliding window of recent conversation history to prevent context explosion and degenerative repetition
            recent_history = history[-6:]
            clean_history = []
            for msg in recent_history:
                role = msg.get("role", "user")
                text = str(msg.get("content", ""))
                # Deduplicate consecutive identical messages
                if clean_history and clean_history[-1]["role"] == role and clean_history[-1]["content"] == text:
                    continue
                clean_history.append({"role": role, "content": text})
            for msg in clean_history:
                messages.append(msg)

        messages.append({"role": "user", "content": str(prompt)})

        req_payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools_schema,
            "stream": False
        }

        try:
            data_bytes = json.dumps(req_payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data_bytes,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            response_msg = result.get("message", {})
            content = response_msg.get("content", "")
            tool_calls = response_msg.get("tool_calls", [])

            sources = []
            artifact = None

            if tool_calls:
                messages.append(response_msg)

                for tool_call in tool_calls:
                    func_obj = tool_call.get("function", {})
                    fn_name = func_obj.get("name")
                    fn_args = func_obj.get("arguments", {})
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

                        # Provide full excerpt up to 1800 characters so critical details are preserved
                        compact_results = []
                        for item in sources:
                            compact_results.append({
                                "title": item.get("title"),
                                "speaker": item.get("speaker"),
                                "excerpt": str(item.get("content", ""))[:1800]
                            })

                        messages.append({
                            "role": "tool",
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
                            "content": json.dumps({
                                "status": "created",
                                "title": res["title"],
                                "artifact_type": res["artifact_type"]
                            })
                        })

                # Turn 2: Follow-up call so model synthesizes evidence into final response
                turn2_payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                data_bytes_2 = json.dumps(turn2_payload).encode("utf-8")
                req2 = urllib.request.Request(
                    f"{self.base_url}/api/chat",
                    data=data_bytes_2,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req2, timeout=90) as resp2:
                    result2 = json.loads(resp2.read().decode("utf-8"))

                content = result2.get("message", {}).get("content", "") or content

                # If artifact was not created via tool call but content has code block, extract it
                if not artifact and content:
                    html_block = re.search(r"```html\s*([\s\S]*?)```", content, re.IGNORECASE)
                    if html_block:
                        try:
                            artifact = create_artifact_domain(
                                title="Generated HTML Component",
                                artifact_type="html",
                                content=html_block.group(1).strip()
                            )
                        except Exception:
                            pass

            else:
                # Robust tool fallback: If 3B model skipped function calling on a factual query due to prior history bias,
                # check if grounded transcript chunks exist for the prompt.
                res = search_transcripts_domain(query=prompt, top_k=5)
                if not res.get("empty_result") and res.get("results"):
                    sources = res.get("results", [])
                    evidence_text = "\n\n".join([
                        f"[{item.get('title', 'Lenny Episode')}] {item.get('speaker', 'Guest')}:\n{str(item.get('content', ''))[:1800]}"
                        for item in sources
                    ])
                    messages.append({
                        "role": "user",
                        "content": (
                            f"Retrieved transcript evidence for '{prompt}':\n\n{evidence_text}\n\n"
                            "Please answer the user's question strictly grounded in this evidence. Cite the episode titles and speakers."
                        )
                    })
                    turn2_payload = {
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                    data_bytes_2 = json.dumps(turn2_payload).encode("utf-8")
                    req2 = urllib.request.Request(
                        f"{self.base_url}/api/chat",
                        data=data_bytes_2,
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req2, timeout=90) as resp2:
                        result2 = json.loads(resp2.read().decode("utf-8"))

                    content = result2.get("message", {}).get("content", "") or content
                elif not content:
                    content = "The available transcripts do not contain information to answer this question."

            # If the assistant determines that the transcripts do not contain information to answer, clear sources
            content_lower = (content or "").lower()
            if any(phrase in content_lower for phrase in [
                "available transcripts do not contain",
                "transcripts do not contain information",
                "do not contain information to answer",
                "transcripts do not mention",
                "not enough information in the transcripts",
                "no information found in the available transcripts"
            ]):
                sources = []
            elif sources:
                # Generic citation refinement: keep chunks from primary relevant episode or high relevance
                primary_title = sources[0].get("title")
                top_score = sources[0].get("score", 0.0)
                filtered = []
                for s in sources:
                    s_title = s.get("title", "")
                    s_score = s.get("score", 0.0)
                    if s_title == primary_title or (top_score > 0 and s_score >= top_score * 0.7):
                        filtered.append(s)
                sources = filtered

            return {
                "content": content or "Response generated by Local Ollama.",
                "sources": sources,
                "artifact": artifact,
                "provider_used": "ollama",
                "model_used": self.model
            }
        except Exception as e:
            raise RuntimeError(f"Ollama execution error: {str(e)}")
