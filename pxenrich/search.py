"""Natural-language question parsing and evidence search.

The parser maps a plain-language question to deterministic filters over the
assertion index plus an FTS query. No LLM is required for retrieval; the LLM
(when configured) only explains what retrieval found.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from .db import get_dataset, load_assertions, row_to_record
from .models import DatasetRecord

# Topic filters the UI exposes as browseable chips. Each maps to assertion filters.
TOPICS = {
    "triple-negative": {"field": "subtype", "value_like": "%TNBC%"},
    "her2": {"field": "her2_status", "any_signal": True},
    "er-positive": {"field": "er_status", "value_like": "positive"},
    "luminal": {"field": "subtype", "value_like": "%luminal%"},
    "tumor-tissue": {"field": "sample_type", "value_like": "%tissue%"},
    "plasma": {"field": "sample_type", "value_like": "%plasma%"},
    "blood": {"field": "sample_type", "value_like": "%blood%"},
    "urine": {"field": "sample_type", "value_like": "%urine%"},
    "cell-line": {"field": "sample_type", "value_like": "%cell line%"},
    "human-patient": {"field": "organism_context", "value_like": "%patient-derived%"},
    "animal-model": {"field": "organism_context", "value_like": "%animal model%"},
    "treatment": {"field": "treatment_context", "any_signal": True},
    "pre-post-treatment": {"field": "treatment_context", "value_like": "%pre/post%"},
}


@dataclass
class ParsedQuery:
    raw: str
    fts_terms: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    human_only: bool = False
    require_known: Optional[str] = None  # field that must have status=asserted


_QUESTION_RULES = [
    (r"triple[\s-]?negative|TNBC", "triple-negative"),
    (r"HER2[\s-]?low|HER2", "her2"),
    (r"\bER[\s-]?positive|ER\+|estrogen receptor", "er-positive"),
    (r"luminal", "luminal"),
    (r"plasma", "plasma"),
    (r"\burine|urinary", "urine"),
    (r"\bblood\b|serum|PBMC|monocyte|lymphocyte", "blood"),
    (r"tumou?r tissue|tissue|biopsy|FFPE", "tumor-tissue"),
    (r"cell[\s-]?lines?", "cell-line"),
    (r"patient[\s-]?derived|in humans|human (?:studies|tumou?rs|samples)|patients", "human-patient"),
    (r"animal|mouse|murine|mice", "animal-model"),
    (r"before and after|pre[\s-]?and[\s-]?post|pre/post", "pre-post-treatment"),
    (r"treatment|therapy|drug response|resistance", "treatment"),
]

_STOPWORDS = set("""a an and are be been can could did do does for from had has have how
in is it its of on or research researchers show me studied studies study that the there
to using was were what which who why with has have does did been exist about know mean
protein proteins proteomics level types kinds public datasets dataset""".split())


def parse_question(q: str) -> ParsedQuery:
    pq = ParsedQuery(raw=q)
    for pat, topic in _QUESTION_RULES:
        if re.search(pat, q, re.I) and topic not in pq.topics:
            pq.topics.append(topic)
    if re.search(r"in humans|human (?:studies|tumou?rs)|patient", q, re.I):
        pq.human_only = True
    if re.search(r"(?:ER|HER2|PR).{0,30}(?:status )?(?:is )?known", q, re.I):
        # "where ER or HER2 status is known" → require asserted receptor status
        pq.require_known = "receptor_status"
    # Residual FTS terms: content words not already captured by a topic.
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", q.lower())
    pq.fts_terms = [w for w in words if w not in _STOPWORDS][:6]
    return pq


def _topic_accessions(conn: sqlite3.Connection, topic: str) -> set[str]:
    spec = TOPICS[topic]
    if spec.get("any_signal"):
        rows = conn.execute(
            """SELECT DISTINCT dataset_accession a FROM assertions
               WHERE field = ? AND (status = 'asserted'
                     OR (status = 'abstained' AND scope = 'study_focus'))""",
            (spec["field"],)).fetchall()
    else:
        rows = conn.execute(
            """SELECT DISTINCT dataset_accession a FROM assertions
               WHERE field = ? AND status IN ('asserted','mixed')
                 AND value LIKE ?""",
            (spec["field"], spec["value_like"])).fetchall()
    return {r["a"] for r in rows}


def search(conn: sqlite3.Connection, question: str, limit: int = 20,
           topics: Optional[list[str]] = None) -> dict:
    """Search the evidence index. Returns records plus retrieval diagnostics."""
    pq = parse_question(question or "")
    if topics:
        for t in topics:
            if t in TOPICS and t not in pq.topics:
                pq.topics.append(t)

    candidate_sets = []
    for t in pq.topics:
        candidate_sets.append(_topic_accessions(conn, t))

    fts_hits: list[str] = []
    if pq.fts_terms:
        match = " OR ".join(f'"{t}"' for t in pq.fts_terms)
        try:
            rows = conn.execute(
                """SELECT accession, rank FROM datasets_fts
                   WHERE datasets_fts MATCH ? ORDER BY rank LIMIT 200""",
                (match,)).fetchall()
            fts_hits = [r["accession"] for r in rows]
        except sqlite3.OperationalError:
            fts_hits = []

    if candidate_sets:
        accs = set.intersection(*candidate_sets) if len(candidate_sets) > 1 \
            else candidate_sets[0]
        # Comparative/enumeration questions ("which are X and which are Y")
        # want the union of categories, not the intersection — likewise when
        # the intersection is empty but individual topics matched.
        if len(candidate_sets) > 1 and (
                not accs or re.search(r"which .+ and which", (question or ""), re.I)):
            accs = set.union(*candidate_sets)
        # Rank topic hits by FTS relevance when available.
        ordered = [a for a in fts_hits if a in accs] + \
                  [a for a in sorted(accs) if a not in fts_hits]
    else:
        ordered = fts_hits

    if pq.human_only and ordered:
        human = _topic_accessions(conn, "human-patient") | {
            r["a"] for r in conn.execute(
                """SELECT DISTINCT dataset_accession a FROM assertions
                   WHERE field='organism_context' AND status='asserted'
                     AND value LIKE 'human%'""").fetchall()}
        ordered = [a for a in ordered if a in human]

    if pq.require_known == "receptor_status" and ordered:
        known = {r["a"] for r in conn.execute(
            """SELECT DISTINCT dataset_accession a FROM assertions
               WHERE field IN ('er_status','her2_status','pr_status')
                 AND status='asserted'""").fetchall()}
        ordered = [a for a in ordered if a in known]

    records: list[DatasetRecord] = []
    for acc in ordered[:limit]:
        rec = get_dataset(conn, acc)
        if rec:
            records.append(rec)

    return {
        "question": question,
        "parsed": {
            "topics": pq.topics,
            "fts_terms": pq.fts_terms,
            "human_only": pq.human_only,
            "require_known": pq.require_known,
        },
        "total_matches": len(ordered),
        "returned": len(records),
        "records": records,
    }


def browse_topic(conn: sqlite3.Connection, topic: str, limit: int = 50) -> list[DatasetRecord]:
    if topic not in TOPICS:
        raise KeyError(f"Unknown topic '{topic}'. Valid topics: {', '.join(TOPICS)}")
    accs = sorted(_topic_accessions(conn, topic))[:limit]
    return [get_dataset(conn, a) for a in accs if a]
