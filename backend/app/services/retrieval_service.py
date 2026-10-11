import math
import re
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from backend.app.db.models import TranscriptChunkModel, TranscriptModel

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "about", "above", "after", "again", "against",
    "all", "am", "an", "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "by", "can't", "cannot", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "him", "how", "if", "in", "into",
    "is", "it", "its", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "other", "our", "out", "over", "own", "same", "so", "than", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "would", "you", "your"
}

class RetrievalService:
    @staticmethod
    def extract_search_terms(query: Any) -> list[str]:
        """Tokenize query and filter stop words to form search terms with safe type coercion."""
        query_str = str(query) if query is not None else ""
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", query_str.lower())
        terms = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        return terms

    @staticmethod
    def search_chunks(db: Session, query: Any, top_k: Any = 5, min_score: float = 0.5) -> dict[str, Any]:
        """BM25 term-frequency and inverse-document-frequency search over indexed transcript chunks."""
        query_str = str(query) if query is not None else ""
        try:
            top_k_int = max(1, int(top_k))
        except (ValueError, TypeError):
            top_k_int = 5

        terms = RetrievalService.extract_search_terms(query_str)
        if not terms:
            return {
                "query": query_str,
                "empty_result": True,
                "results": [],
                "message": "Query contains no search terms."
            }

        # Build SQL OR conditions for terms
        clause_list = []
        for term in terms:
            clause_list.append(TranscriptChunkModel.content.ilike(f"%{term}%"))

        stmt = (
            select(TranscriptChunkModel, TranscriptModel)
            .join(TranscriptModel, TranscriptChunkModel.transcript_id == TranscriptModel.id)
            .where(or_(*clause_list))
        )

        rows = db.execute(stmt).all()
        if not rows:
            return {
                "query": query_str,
                "empty_result": True,
                "results": [],
                "message": f"No transcript chunks matched terms: {terms}"
            }

        # Total number of chunks in the database for IDF calculation
        total_chunks = db.query(func.count(TranscriptChunkModel.id)).scalar() or len(rows)

        # Calculate IDF for each term based on frequency in matching chunks
        idf_map = {}
        for term in set(terms):
            doc_freq = sum(1 for chunk_obj, _ in rows if term in chunk_obj.content.lower())
            if doc_freq > 0:
                idf_map[term] = max(0.1, math.log((total_chunks - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0))
            else:
                idf_map[term] = 0.0

        # Calculate average document word length
        chunk_word_lens = [len(c.content.split()) for c, _ in rows]
        avg_doc_len = (sum(chunk_word_lens) / len(chunk_word_lens)) if chunk_word_lens else 100.0

        scored_results = []
        query_lower = query_str.lower()
        seen_snippets = set()

        k1 = 1.2
        b = 0.75

        for chunk_obj, transcript_obj in rows:
            # Deduplicate by content snippet so identical copies are skipped
            snippet_key = chunk_obj.content[:80].strip()
            if snippet_key in seen_snippets:
                continue
            seen_snippets.add(snippet_key)

            content_lower = chunk_obj.content.lower()
            meta = chunk_obj.chunk_metadata or {}
            meta_text = f"{meta.get('title', '')} {meta.get('guest', '')} {transcript_obj.title or ''} {chunk_obj.speaker or ''}".lower()

            doc_len = len(chunk_obj.content.split())
            len_norm = 1.0 - b + b * (doc_len / avg_doc_len)

            chunk_score = 0.0
            distinct_terms_matched = 0

            for term in set(terms):
                cnt = content_lower.count(term)
                meta_cnt = meta_text.count(term)
                effective_cnt = cnt + (meta_cnt * 2)

                if effective_cnt > 0:
                    distinct_terms_matched += 1
                    idf = idf_map.get(term, 0.0)
                    tf_component = (effective_cnt * (k1 + 1.0)) / (effective_cnt + k1 * len_norm)
                    chunk_score += tf_component * idf

            # If query has 3 or more terms, require at least 2 distinct terms (unless exact phrase match)
            is_phrase_match = query_lower in content_lower
            if len(terms) >= 3 and distinct_terms_matched < 2 and not is_phrase_match:
                continue

            if chunk_score <= 0.0:
                continue

            # Exact phrase bonus
            if is_phrase_match:
                chunk_score += 3.0

            scored_results.append({
                "chunk_id": chunk_obj.id,
                "title": meta.get("title") or transcript_obj.title,
                "guest": meta.get("guest") or chunk_obj.speaker or "Guest",
                "source_url": meta.get("youtube_url") or transcript_obj.source_url,
                "speaker": chunk_obj.speaker,
                "content": chunk_obj.content,
                "score": round(chunk_score, 3)
            })

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:top_k_int]

        highest_score = top_results[0]["score"] if top_results else 0.0
        if highest_score < min_score:
            return {
                "query": query_str,
                "empty_result": True,
                "results": [],
                "message": f"Retrieval score {highest_score} is below threshold {min_score}."
            }

        return {
            "query": query_str,
            "empty_result": False,
            "results": top_results,
            "message": f"Retrieved {len(top_results)} relevant transcript chunks."
        }

