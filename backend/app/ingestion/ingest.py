import os
import re
import yaml
import urllib.request
from typing import Any
from sqlalchemy.orm import Session
from backend.app.db.database import SessionLocal, init_db
from backend.app.db.models import TranscriptModel, TranscriptChunkModel

SAMPLE_EPISODES = [
    {
        "guest": "brian-chesky",
        "url": "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes/brian-chesky/transcript.md"
    },
    {
        "guest": "shreyas-doshi",
        "url": "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes/shreyas-doshi/transcript.md"
    },
    {
        "guest": "marty-cagan",
        "url": "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes/marty-cagan/transcript.md"
    },
    {
        "guest": "elena-verna",
        "url": "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes/elena-verna/transcript.md"
    }
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
    # Split text by speaker or paragraph markers
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

def ingest_transcript_from_text(db: Session, raw_text: str, default_title: str = "Lenny Podcast Episode", source_url: str | None = None) -> TranscriptModel:
    """Parse, chunk, and persist a single transcript to database."""
    frontmatter, body = parse_transcript_markdown(raw_text)

    title = frontmatter.get("title") or default_title
    guest = frontmatter.get("guest")
    yt_url = frontmatter.get("youtube_url") or source_url

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

def run_sample_ingestion(db: Session | None = None) -> int:
    """Download and ingest sample representative transcripts from GitHub archive."""
    close_db = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db = True

    ingested_count = 0
    try:
        for item in SAMPLE_EPISODES:
            try:
                req = urllib.request.urlopen(item["url"], timeout=10)
                raw_text = req.read().decode("utf-8")
                ingest_transcript_from_text(
                    db,
                    raw_text,
                    default_title=f"Lenny's Podcast - {item['guest']}",
                    source_url=item["url"]
                )
                ingested_count += 1
            except Exception as e:
                print(f"Failed to fetch sample transcript for {item['guest']}: {e}")
    finally:
        if close_db:
            db.close()

    return ingested_count

if __name__ == "__main__":
    print("🚀 Running sample transcript ingestion...")
    count = run_sample_ingestion()
    print(f"✅ Ingested {count} transcripts successfully!")
