import os
import re
import yaml
import time
import json
import logging
import asyncio
import urllib.request
import urllib.error
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models import TranscriptModel, TranscriptChunkModel

logger = logging.getLogger(__name__)

# Upstream repository constants
UPSTREAM_REPO = "ChatPRD/lennys-podcast-transcripts"
JSDELIVR_FLAT_API = f"https://data.jsdelivr.net/v1/package/gh/{UPSTREAM_REPO}@main/flat"
GITHUB_TREE_API = f"https://api.github.com/repos/{UPSTREAM_REPO}/git/trees/main?recursive=1"
CDN_BASE_URL = f"https://cdn.jsdelivr.net/gh/{UPSTREAM_REPO}@main"
RAW_GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/main"

# Seed episodes for offline fallback
SEED_EPISODES = [
    {
        "slug": "brian-chesky",
        "title": "Brian Chesky's new playbook",
        "url": f"{CDN_BASE_URL}/episodes/brian-chesky/transcript.md",
        "fallback_url": f"{RAW_GITHUB_BASE_URL}/episodes/brian-chesky/transcript.md"
    },
    {
        "slug": "shreyas-doshi",
        "title": "Why Most Execution Problems are Strategy Problems | Shreyas Doshi",
        "url": f"{CDN_BASE_URL}/episodes/shreyas-doshi/transcript.md",
        "fallback_url": f"{RAW_GITHUB_BASE_URL}/episodes/shreyas-doshi/transcript.md"
    },
    {
        "slug": "marty-cagan",
        "title": "The Nature of Product | Marty Cagan",
        "url": f"{CDN_BASE_URL}/episodes/marty-cagan/transcript.md",
        "fallback_url": f"{RAW_GITHUB_BASE_URL}/episodes/marty-cagan/transcript.md"
    },
    {
        "slug": "elena-verna",
        "title": "Elena Verna on PLG, B2B Growth, and Marketing",
        "url": f"{CDN_BASE_URL}/episodes/elena-verna/transcript.md",
        "fallback_url": f"{RAW_GITHUB_BASE_URL}/episodes/elena-verna/transcript.md"
    }
]

# Backward compatibility alias
SAMPLE_EPISODES = [
    {"guest": item["slug"], "url": item["fallback_url"]}
    for item in SEED_EPISODES
]


def parse_transcript_markdown(raw_text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and raw body content from transcript Markdown."""
    parts = raw_text.split("---")
    if len(parts) >= 3:
        try:
            frontmatter = yaml.safe_load(parts[1])
            body = "---".join(parts[2:]).strip()
            return frontmatter or {}, body
        except Exception:
            pass
    return {}, raw_text.strip()


def chunk_transcript_text(body_text: str, max_chunk_words: int = 400, overlap_words: int = 50) -> list[dict[str, Any]]:
    """Semantically chunk transcript text respecting speaker headers and paragraph breaks."""
    paragraphs = [p.strip() for p in body_text.split("\n\n") if p.strip()]
    
    chunks = []
    current_words = []
    current_speaker = "Unknown"

    for p in paragraphs:
        # Check for speaker timestamp pattern e.g. "Brian Chesky (00:05:04):"
        speaker_match = re.match(r"^([A-Za-z\s]+)\s*\(\d{2}:\d{2}:\d{2}\):", p)
        if speaker_match:
            current_speaker = speaker_match.group(1).strip()

        words = p.split()
        if len(current_words) + len(words) > max_chunk_words and current_words:
            chunk_content = " ".join(current_words)
            chunks.append({
                "content": chunk_content,
                "speaker": current_speaker
            })
            # Preserve overlap
            current_words = current_words[-overlap_words:] + words
        else:
            current_words.extend(words)

    if current_words:
        chunks.append({
            "content": " ".join(current_words),
            "speaker": current_speaker
        })

    return chunks


def ingest_transcript_from_text(
    db: Session,
    raw_text: str,
    default_title: str = "Lenny Podcast Episode",
    source_url: str | None = None
) -> TranscriptModel:
    """Parse, chunk, and persist a single transcript to database."""
    frontmatter, body = parse_transcript_markdown(raw_text)

    title = frontmatter.get("title") or default_title
    guest = frontmatter.get("guest")
    yt_url = source_url or frontmatter.get("youtube_url")

    # Check for existing transcript to prevent duplicates
    existing = db.query(TranscriptModel).filter(
        (TranscriptModel.title == title) | (TranscriptModel.source_url == yt_url)
    ).first()
    if existing:
        return existing
    
    transcript = TranscriptModel(
        title=title,
        source_url=yt_url,
        raw_text=body
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    # Chunk body
    chunks_data = chunk_transcript_text(body)
    for idx, chunk_info in enumerate(chunks_data):
        chunk_obj = TranscriptChunkModel(
            transcript_id=transcript.id,
            chunk_index=idx,
            content=chunk_info["content"],
            speaker=chunk_info.get("speaker") or guest,
            chunk_metadata={
                "title": title,
                "guest": guest,
                "youtube_url": yt_url,
                "chunk_id": f"{transcript.id}_chunk_{idx}"
            }
        )
        db.add(chunk_obj)

    db.commit()
    return transcript


def discover_all_transcripts() -> list[dict[str, str]]:
    """
    Dynamically discover all available podcast transcripts from the upstream collection.
    Tries primary CDN directory index, falls back to GitHub Trees API, and lastly to seed episodes.
    """
    # 1. Try jsDelivr CDN directory index (High reliability, Cloudflare edge, full upstream episode collection)
    try:
        cdn_dir_url = f"{CDN_BASE_URL}/episodes/"
        req = urllib.request.Request(
            cdn_dir_url,
            headers={"User-Agent": "LennyGrowthAssistant/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            slugs = list(dict.fromkeys(
                re.findall(r"/gh/ChatPRD/lennys-podcast-transcripts@main/episodes/([^/\"\'\s]+)/", html)
            ))
            if slugs:
                episodes = []
                for slug in slugs:
                    path = f"/episodes/{slug}/transcript.md"
                    episodes.append({
                        "slug": slug,
                        "title": slug.replace("-", " ").title(),
                        "path": path,
                        "url": f"{CDN_BASE_URL}{path}",
                        "fallback_url": f"{RAW_GITHUB_BASE_URL}{path}"
                    })
                logger.info(f"Discovered {len(episodes)} transcripts via jsDelivr CDN directory index.")
                return sorted(episodes, key=lambda x: x["slug"])
    except Exception as e:
        logger.warning(f"jsDelivr CDN directory discovery failed: {e}. Trying flat package API...")

    # 2. Try jsDelivr flat package API (fast, reliable, bypasses rate limits)
    try:
        req = urllib.request.Request(
            JSDELIVR_FLAT_API,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LennyGrowthAssistant/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            files = data.get("files", [])
            episodes = []
            for item in files:
                path = item.get("name", "")
                if path.startswith("/episodes/") and path.endswith("/transcript.md"):
                    # Extract slug: /episodes/<slug>/transcript.md
                    parts = path.strip("/").split("/")
                    if len(parts) >= 2:
                        slug = parts[1]
                        episodes.append({
                            "slug": slug,
                            "title": slug.replace("-", " ").title(),
                            "path": path,
                            "url": f"{CDN_BASE_URL}{path}",
                            "fallback_url": f"{RAW_GITHUB_BASE_URL}{path}"
                        })
            if episodes:
                logger.info(f"Discovered {len(episodes)} transcripts via jsDelivr API.")
                return sorted(episodes, key=lambda x: x["slug"])
    except Exception as e:
        logger.warning(f"jsDelivr transcript discovery failed: {e}. Trying GitHub Trees API...")

    # 3. Try GitHub Git Trees API
    try:
        req = urllib.request.Request(
            GITHUB_TREE_API,
            headers={"User-Agent": "LennyGrowthAssistant/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tree = data.get("tree", [])
            episodes = []
            for item in tree:
                path = item.get("path", "")
                if path.startswith("episodes/") and path.endswith("/transcript.md"):
                    slug = path.split("/")[1]
                    episodes.append({
                        "slug": slug,
                        "title": slug.replace("-", " ").title(),
                        "path": f"/{path}",
                        "url": f"{CDN_BASE_URL}/{path}",
                        "fallback_url": f"{RAW_GITHUB_BASE_URL}/{path}"
                    })
            if episodes:
                logger.info(f"Discovered {len(episodes)} transcripts via GitHub Trees API.")
                return sorted(episodes, key=lambda x: x["slug"])
    except Exception as e:
        logger.warning(f"GitHub Trees transcript discovery failed: {e}. Falling back to seed collection.")

    # 4. Fallback to seed episodes if completely offline
    logger.info(f"Using {len(SEED_EPISODES)} bootstrap seed episodes.")
    return SEED_EPISODES


def _safe_quote_url(url: str) -> str:
    """Safely percent-encode path components of URLs with non-ASCII characters."""
    import urllib.parse
    try:
        parsed = urllib.parse.urlsplit(url)
        quoted_path = urllib.parse.quote(parsed.path, safe="/@")
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, quoted_path, parsed.query, parsed.fragment))
    except Exception:
        return url


def _fetch_transcript_text(url: str, fallback_url: str | None = None, max_retries: int = 3) -> str:
    """Download transcript text with bounded exponential backoff and URL fallback."""
    urls = [_safe_quote_url(url)]
    if fallback_url and fallback_url != url:
        urls.append(_safe_quote_url(fallback_url))

    for candidate_url in urls:
        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(
                    candidate_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LennyGrowthAssistant/1.0"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.read().decode("utf-8")
            except Exception as e:
                if attempt == max_retries:
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {candidate_url}: {e}")
                else:
                    time.sleep(0.5 * (2 ** (attempt - 1)))

    raise RuntimeError(f"Unable to download transcript after retries from {urls}")


class IngestionManager:
    """
    Manages non-blocking background discovery, ingestion, chunking,
    and indexing of the complete Lenny's Podcast transcript collection.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.status: str = "idle"  # "idle", "discovering", "indexing", "ready", "error"
        self.discovered_count: int = 0
        self.processed_count: int = 0
        self.total_chunks: int = 0
        self.current_episode: str | None = None
        self.failed_episodes: list[dict[str, str]] = []
        self.is_running: bool = False
        self.error_message: str | None = None
        self._background_task: asyncio.Task | None = None

    def get_status(self, db: Session | None = None) -> dict[str, Any]:
        """Return real-time ingestion status and database counts."""
        db_provided = db is not None
        if not db_provided:
            db = SessionLocal()

        try:
            stored_transcripts = db.query(func.count(TranscriptModel.id)).scalar() or 0
            stored_chunks = db.query(func.count(TranscriptChunkModel.id)).scalar() or 0
        finally:
            if not db_provided:
                db.close()

        # Update in-memory counts if idle or ready
        if self.status in ("idle", "ready") and stored_transcripts > 0:
            self.processed_count = max(self.processed_count, stored_transcripts)
            self.total_chunks = max(self.total_chunks, stored_chunks)
            if self.discovered_count == 0:
                self.discovered_count = self.processed_count

        return {
            "status": self.status,
            "is_running": self.is_running,
            "discovered_count": self.discovered_count,
            "processed_count": stored_transcripts,
            "total_chunks": stored_chunks,
            "current_episode": self.current_episode,
            "failed_count": len(self.failed_episodes),
            "error_message": self.error_message,
            "ready": self.status == "ready" or (not self.is_running and stored_transcripts > 0)
        }

    async def start_background_ingestion(self, max_batch: int | None = None) -> None:
        """
        Trigger idempotent, non-blocking background ingestion.
        Guarantees that application startup yields immediately without waiting.
        """
        if self.is_running:
            logger.info("Ingestion is already running in background.")
            return

        self.is_running = True
        self.status = "discovering"
        self.error_message = None

        # Run worker as detached asyncio task
        self._background_task = asyncio.create_task(self._worker(max_batch))

    async def _worker(self, max_batch: int | None = None) -> None:
        """Async background worker processing transcripts safely in batches."""
        logger.info("Starting background transcript ingestion worker...")
        try:
            # 1. Discover all available transcripts
            episodes = await asyncio.to_thread(discover_all_transcripts)
            self.discovered_count = len(episodes)
            self.status = "indexing"
            logger.info(f"Discovered {self.discovered_count} transcripts. Checking existing index...")

            # 2. Get list of already indexed source URLs and titles
            db = SessionLocal()
            try:
                existing_urls = set(
                    url for (url,) in db.query(TranscriptModel.source_url).all() if url
                )
                existing_titles = set(
                    title for (title,) in db.query(TranscriptModel.title).all() if title
                )
                self.processed_count = len(existing_titles)
                self.total_chunks = db.query(func.count(TranscriptChunkModel.id)).scalar() or 0
            finally:
                db.close()

            # Limit if max_batch requested
            target_episodes = episodes[:max_batch] if max_batch else episodes

            # 3. Process unindexed transcripts one by one
            for item in target_episodes:
                slug = item["slug"]
                url = item["url"]
                fallback_url = item.get("fallback_url")

                # Skip if already indexed
                if url in existing_urls or fallback_url in existing_urls or item["title"] in existing_titles:
                    continue

                self.current_episode = item["title"]

                # Download and ingest in thread to avoid blocking asyncio event loop
                try:
                    await self._ingest_single_episode(item)
                    self.processed_count += 1
                except Exception as ep_err:
                    logger.warning(f"Failed to ingest episode '{slug}': {ep_err}")
                    self.failed_episodes.append({"slug": slug, "error": str(ep_err)})

                # Brief non-blocking yield to keep event loop and database connections responsive
                await asyncio.sleep(0.05)

            self.status = "ready"
            self.current_episode = None
            logger.info(f"Background ingestion completed. Processed: {self.processed_count}, Chunks: {self.total_chunks}")
        except Exception as e:
            logger.exception(f"Fatal error during background transcript ingestion: {e}")
            self.status = "error"
            self.error_message = str(e)
        finally:
            self.is_running = False

    async def _ingest_single_episode(self, item: dict[str, str]) -> None:
        """Download, parse, and persist a single episode."""
        raw_text = await asyncio.to_thread(
            _fetch_transcript_text,
            item["url"],
            item.get("fallback_url")
        )

        def _db_save():
            db = SessionLocal()
            try:
                transcript = ingest_transcript_from_text(
                    db,
                    raw_text,
                    default_title=item["title"],
                    source_url=item["url"]
                )
                chunk_count = db.query(TranscriptChunkModel).filter(
                    TranscriptChunkModel.transcript_id == transcript.id
                ).count()
                return chunk_count
            finally:
                db.close()

        new_chunks = await asyncio.to_thread(_db_save)
        self.total_chunks += new_chunks


# Global singleton ingestion manager
ingestion_manager = IngestionManager()


def run_sample_ingestion(db: Session | None = None) -> int:
    """Download and ingest sample representative transcripts from GitHub archive."""
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True

    ingested_count = 0
    try:
        for item in SEED_EPISODES:
            try:
                raw_text = _fetch_transcript_text(item["url"], item.get("fallback_url"))
                ingest_transcript_from_text(
                    db,
                    raw_text,
                    default_title=item["title"],
                    source_url=item["url"]
                )
                ingested_count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest seed transcript {item['slug']}: {e}")
    finally:
        if close_db:
            db.close()

    return ingested_count


if __name__ == "__main__":
    print("🚀 Discovering all podcast transcripts...")
    found = discover_all_transcripts()
    print(f"✅ Discovered {len(found)} transcripts!")
    print("🚀 Ingesting sample transcripts...")
    count = run_sample_ingestion()
    print(f"✅ Seeded {count} transcripts successfully!")
