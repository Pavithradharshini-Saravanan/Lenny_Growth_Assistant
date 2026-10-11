import re
import warnings
from typing import Any
import bleach
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.services.retrieval_service import RetrievalService
from backend.app.skills.ship30 import Ship30WritingSkill

class SearchTranscriptsArgs(BaseModel):
    query: str = Field(..., description="Product or growth topic/question to search in transcripts")
    top_k: int = Field(5, description="Number of transcript chunks to retrieve")

class Ship30SkillArgs(BaseModel):
    topic: str = Field(..., description="Core thesis or question for the Ship 30 for 30 essay")
    audience: str = Field("Product and Growth Practitioners", description="Target audience")

class CreateArtifactArgs(BaseModel):
    title: str = Field(..., description="Title of the artifact")
    artifact_type: str = Field(..., description="'markdown' or 'html'")
    content: str = Field(..., description="Markdown or HTML code content")

def search_transcripts_domain(db: Session | None = None, query: str = "", top_k: int = 5) -> dict[str, Any]:
    """Execute real grounded retrieval over indexed transcript content with safe type coercion."""
    query_str = str(query) if query is not None else ""
    try:
        top_k_int = int(top_k)
    except (ValueError, TypeError):
        top_k_int = 5

    if db is None:
        from backend.app.db.database import SessionLocal
        db = SessionLocal()
        try:
            return RetrievalService.search_chunks(db, query=query_str, top_k=top_k_int)
        finally:
            db.close()

    return RetrievalService.search_chunks(db, query=query_str, top_k=top_k_int)

def sanitize_html_artifact(html_content: str) -> str:
    """
    Sanitize untrusted HTML/CSS artifacts:
    1. Neutralize attempts to escape iframe sandbox, hijack parent window, or access credentials/storage.
    2. Disallow javascript: and data: pseudo-protocols.
    3. Strip dangerous event handlers (onerror, onload, onclick, etc.).
    4. Preserve rich HTML5 structure, CSS formatting, and SVG graphics.
    """
    content = str(html_content or "")

    # Block attempts to target parent frame, cookies, or local/session storage
    dangerous_patterns = [
        r"window\.parent",
        r"parent\.document",
        r"top\.location",
        r"window\.top",
        r"document\.cookie",
        r"localStorage",
        r"sessionStorage",
        r"javascript\s*:",
        r"data\s*:\s*text/html"
    ]
    for pattern in dangerous_patterns:
        content = re.sub(pattern, "/* blocked_security_violation */", content, flags=re.IGNORECASE)

    allowed_tags = [
        "html", "head", "body", "title", "style", "div", "span", "p", "h1", "h2", "h3",
        "h4", "h5", "h6", "b", "strong", "i", "em", "u", "s", "blockquote", "pre", "code",
        "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "a", "img",
        "button", "input", "label", "select", "option", "textarea", "form",
        "svg", "path", "circle", "rect", "line", "polyline", "polygon", "text", "g",
        "canvas", "hr", "br", "section", "article", "nav", "aside", "header", "footer", "main"
    ]
    allowed_attrs = {
        "*": ["class", "id", "style", "title", "width", "height", "name", "value", "placeholder"],
        "a": ["href", "target"],
        "img": ["src", "alt"],
        "svg": ["viewBox", "xmlns", "fill", "stroke", "stroke-width"],
        "path": ["d", "fill", "stroke"],
        "circle": ["cx", "cy", "r", "fill"],
        "rect": ["x", "y", "width", "height", "rx", "ry", "fill"]
    }
    allowed_protocols = ["http", "https", "mailto"]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cleaned = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            protocols=allowed_protocols,
            strip=False
        )
    return cleaned

def run_ship30_skill_domain(topic: str, audience: str = "Product Practitioners", db: Session | None = None) -> dict[str, Any]:
    """Pure domain service for executing Ship 30 for 30 writing transformation using transcript evidence."""
    return Ship30WritingSkill.generate_essay(topic=topic, audience=audience, db_session=db)

def create_artifact_domain(title: str, artifact_type: str, content: str) -> dict[str, Any]:
    """Pure domain service for validating, sanitizing, and creating an artifact."""
    valid_types = ["markdown", "html"]
    type_str = str(artifact_type or "markdown").lower()
    if type_str not in valid_types:
        raise ValueError(f"Invalid artifact_type '{artifact_type}'. Must be one of {valid_types}")

    sanitized_content = str(content or "")
    if type_str == "html":
        sanitized_content = sanitize_html_artifact(sanitized_content)

    return {
        "title": str(title or "Artifact"),
        "artifact_type": type_str,
        "content": sanitized_content
    }

