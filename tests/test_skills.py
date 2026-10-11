import pytest
from backend.app.skills.ship30 import Ship30WritingSkill, SHIP30_GUIDE_URL
from backend.app.tools.base import run_ship30_skill_domain
from backend.app.db.database import SessionLocal
from backend.app.db.models import TranscriptModel, TranscriptChunkModel

@pytest.fixture
def seeded_db(db_session):
    """Seed test database with the 4 canonical podcast transcripts."""
    prod_db = SessionLocal()
    try:
        transcripts = prod_db.query(TranscriptModel).all()
        for t in transcripts:
            new_t = TranscriptModel(
                id=t.id,
                title=t.title,
                source_url=t.source_url,
                raw_text=t.raw_text
            )
            db_session.add(new_t)
            for c in t.chunks:
                new_c = TranscriptChunkModel(
                    id=c.id,
                    transcript_id=c.transcript_id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    speaker=c.speaker,
                    chunk_metadata=c.chunk_metadata
                )
                db_session.add(new_c)
        db_session.commit()
    finally:
        prod_db.close()
    return db_session


def test_ship30_skill_guide_url_documented():
    """Verify that the Ship 30 for 30 source guide URL is documented and valid."""
    assert SHIP30_GUIDE_URL is not None
    assert "ship30for30.com" in SHIP30_GUIDE_URL


@pytest.mark.parametrize("topic,expected_speaker_cue", [
    ("Reducing Onboarding Friction in Product-Led Growth", "Elena Verna"),
    ("Empowered Product Teams vs Feature Factories", "Marty Cagan"),
    ("Airbnb Release Cycles and Product Roadmaps", "Brian Chesky"),
    ("Why Most Execution Problems are Strategy Problems", "Shreyas Doshi")
])
def test_ship30_essay_structure_and_grounding(seeded_db, topic, expected_speaker_cue):
    """
    Verify the Ship 30 writing skill generates a complete essay meeting all assignment requirements:
    - Compelling hook with core tension
    - Narrative progression through 5 distinct pillars
    - Skimmable formatting (H1, H2, H3, selective bolding, bulleted checklists)
    - Practitioner actionable takeaway
    - Factual grounding in real transcript evidence
    - Verified word count tolerance around 1,250 words (1,100 - 1,400)
    """
    res = Ship30WritingSkill.generate_essay(topic=topic, db_session=seeded_db)

    # 1. Title and Metadata
    assert "title" in res
    assert res["methodology"] == "Ship 30 for 30"
    content = res["content"]

    # 2. Target Word Count Check (1,100 to 1,400 words)
    words = content.split()
    word_count = len(words)
    assert 1100 <= word_count <= 1400, f"Word count {word_count} is outside tolerance [1100, 1400] for topic '{topic}'"
    assert res["word_count"] == word_count

    # 3. Hook & Core Tension Check
    assert "## 1. The Core Tension" in content
    assert "**" in content  # Selective bold emphasis
    assert "operational breakdowns" in content.lower() or "tension" in content.lower()

    # 4. Narrative Progression Check
    assert "## 2. The Hidden Failure Mode" in content
    assert "## 3. The Frontline Evidence" in content
    assert "## 4. The Operational Blueprint" in content
    assert "### Pillar 1:" in content
    assert "### Pillar 5:" in content

    # 5. Practitioner Actionable Takeaway Checklist
    assert "## 5. The Practitioner Playbook" in content
    assert "Actionable Takeaways" in content
    assert "1. **" in content  # Bulleted/numbered action items
    assert "The Ultimate Takeaway" in content

    # 6. Source Grounding & Attribution
    assert "## Sources & Transcript Evidence" in content
    assert len(res["sources"]) > 0
    # Confirm speaker cue is identified in content or sources
    content_lower = content.lower()
    assert expected_speaker_cue.lower() in content_lower


def test_ship30_domain_tool_wrapper(seeded_db):
    """Verify that run_ship30_skill_domain tool executes cleanly and returns structured output."""
    res = run_ship30_skill_domain(topic="Managing Product Risk", audience="Tech Leads", db=seeded_db)
    assert isinstance(res, dict)
    assert res["audience"] == "Tech Leads"
    assert 1100 <= res["word_count"] <= 1400
    assert "The Operating Playbook for Managing Product Risk" in res["title"]


def test_ship30_novel_unseen_topic_dynamic_handling(seeded_db):
    """Anti-hardcoding test: ensure an unseen novel topic is synthesized dynamically without error."""
    novel_topic = "Continuous discovery habits and customer interview cadences"
    res = Ship30WritingSkill.generate_essay(topic=novel_topic, db_session=seeded_db)
    assert 1100 <= res["word_count"] <= 1400
    assert "Continuous Discovery" in res["title"]
    assert "Pillar 1" in res["content"]
