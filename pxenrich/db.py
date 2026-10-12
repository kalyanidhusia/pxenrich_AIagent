"""SQLite evidence index with FTS5 full-text search.

Schema mirrors the models: a datasets table, an assertions table (one row per
evidence field per dataset, provenance included), and an FTS index over the
searchable text. SQLite keeps v1 dependency-free; the schema is plain SQL so
a later move to Postgres is mechanical.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Optional

from .models import AssertionStatus, DatasetRecord, EvidenceAssertion, Scope, SourceType

DEFAULT_DB = os.environ.get(
    "PXENRICH_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "data", "pxenrich.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    accession TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    repository TEXT NOT NULL,
    species TEXT,
    instrument TEXT,
    announce_date TEXT,
    keywords TEXT,
    description TEXT,
    lab_head TEXT,
    pubmed_ids TEXT,
    dois TEXT,
    repo_link TEXT,
    px_link TEXT,
    source TEXT NOT NULL DEFAULT 'proteomecentral',
    source_retrieved TEXT,
    record_status TEXT NOT NULL DEFAULT 'metadata_only'
);

CREATE TABLE IF NOT EXISTS assertions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_accession TEXT NOT NULL REFERENCES datasets(accession) ON DELETE CASCADE,
    field TEXT NOT NULL,
    value TEXT,
    status TEXT NOT NULL,
    scope TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    evidence_text TEXT,
    source_type TEXT,
    source_url TEXT,
    extracted_by TEXT NOT NULL,
    note TEXT,
    UNIQUE (dataset_accession, field, extracted_by)
);

CREATE INDEX IF NOT EXISTS idx_assert_field_value ON assertions(field, value);
CREATE INDEX IF NOT EXISTS idx_assert_acc ON assertions(dataset_accession);

CREATE VIRTUAL TABLE IF NOT EXISTS datasets_fts USING fts5(
    accession UNINDEXED, title, keywords, description,
    content='datasets', content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS datasets_ai AFTER INSERT ON datasets BEGIN
    INSERT INTO datasets_fts(rowid, accession, title, keywords, description)
    VALUES (new.rowid, new.accession, new.title, new.keywords, new.description);
END;
CREATE TRIGGER IF NOT EXISTS datasets_ad AFTER DELETE ON datasets BEGIN
    INSERT INTO datasets_fts(datasets_fts, rowid, accession, title, keywords, description)
    VALUES ('delete', old.rowid, old.accession, old.title, old.keywords, old.description);
END;
CREATE TRIGGER IF NOT EXISTS datasets_au AFTER UPDATE ON datasets BEGIN
    INSERT INTO datasets_fts(datasets_fts, rowid, accession, title, keywords, description)
    VALUES ('delete', old.rowid, old.accession, old.title, old.keywords, old.description);
    INSERT INTO datasets_fts(rowid, accession, title, keywords, description)
    VALUES (new.rowid, new.accession, new.title, new.keywords, new.description);
END;

CREATE TABLE IF NOT EXISTS tool_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    channel TEXT NOT NULL,          -- api | mcp
    tool TEXT NOT NULL,
    params_json TEXT,
    result_count INTEGER
);
"""


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_record(conn: sqlite3.Connection, rec: DatasetRecord) -> None:
    conn.execute(
        """INSERT INTO datasets (accession, title, repository, species, instrument,
             announce_date, keywords, description, lab_head, pubmed_ids, dois,
             repo_link, px_link, source, source_retrieved, record_status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(accession) DO UPDATE SET
             title=excluded.title, repository=excluded.repository,
             species=excluded.species, instrument=excluded.instrument,
             announce_date=excluded.announce_date, keywords=excluded.keywords,
             description=COALESCE(excluded.description, datasets.description),
             lab_head=COALESCE(excluded.lab_head, datasets.lab_head),
             pubmed_ids=COALESCE(excluded.pubmed_ids, datasets.pubmed_ids),
             dois=COALESCE(excluded.dois, datasets.dois),
             repo_link=COALESCE(excluded.repo_link, datasets.repo_link),
             px_link=excluded.px_link, source=excluded.source,
             source_retrieved=excluded.source_retrieved,
             record_status=excluded.record_status""",
        (rec.accession, rec.title, rec.repository, rec.species, rec.instrument,
         rec.announce_date, rec.keywords, rec.description, rec.lab_head,
         rec.pubmed_ids, rec.dois, rec.repo_link, rec.px_link, rec.source,
         rec.source_retrieved, rec.record_status),
    )
    for a in rec.assertions:
        conn.execute(
            """INSERT INTO assertions (dataset_accession, field, value, status, scope,
                 confidence, evidence_text, source_type, source_url, extracted_by, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(dataset_accession, field, extracted_by) DO UPDATE SET
                 value=excluded.value, status=excluded.status, scope=excluded.scope,
                 confidence=excluded.confidence, evidence_text=excluded.evidence_text,
                 source_type=excluded.source_type, source_url=excluded.source_url,
                 note=excluded.note""",
            (a.dataset_accession, a.field, a.value, a.status.value, a.scope.value,
             a.confidence, a.evidence_text,
             a.source_type.value if a.source_type else None,
             a.source_url, a.extracted_by, a.note),
        )


def row_to_record(row: sqlite3.Row) -> DatasetRecord:
    return DatasetRecord(
        accession=row["accession"], title=row["title"], repository=row["repository"],
        species=row["species"], instrument=row["instrument"],
        announce_date=row["announce_date"], keywords=row["keywords"],
        description=row["description"], lab_head=row["lab_head"],
        pubmed_ids=row["pubmed_ids"], dois=row["dois"], repo_link=row["repo_link"],
        px_link=row["px_link"], source=row["source"],
        source_retrieved=row["source_retrieved"], record_status=row["record_status"],
    )


def load_assertions(conn, accession: str) -> list[EvidenceAssertion]:
    rows = conn.execute(
        "SELECT * FROM assertions WHERE dataset_accession = ? ORDER BY field",
        (accession,)).fetchall()
    out = []
    for r in rows:
        out.append(EvidenceAssertion(
            dataset_accession=r["dataset_accession"], field=r["field"],
            value=r["value"], status=AssertionStatus(r["status"]),
            scope=Scope(r["scope"]), confidence=r["confidence"],
            evidence_text=r["evidence_text"],
            source_type=SourceType(r["source_type"]) if r["source_type"] else None,
            source_url=r["source_url"], extracted_by=r["extracted_by"], note=r["note"],
        ))
    return out


def get_dataset(conn, accession: str) -> Optional[DatasetRecord]:
    row = conn.execute("SELECT * FROM datasets WHERE accession = ?",
                       (accession,)).fetchone()
    if not row:
        return None
    rec = row_to_record(row)
    rec.assertions = load_assertions(conn, accession)
    return rec


def log_tool_call(conn, channel: str, tool: str, params: dict, result_count: int) -> None:
    """Reproducibility log: tool calls and decisions, no personal health data."""
    conn.execute(
        "INSERT INTO tool_log (channel, tool, params_json, result_count) VALUES (?,?,?,?)",
        (channel, tool, json.dumps(params, default=str), result_count))
    conn.commit()


def stats(conn) -> dict:
    n = conn.execute("SELECT COUNT(*) c FROM datasets").fetchone()["c"]
    by_repo = {r["repository"]: r["c"] for r in conn.execute(
        "SELECT repository, COUNT(*) c FROM datasets GROUP BY repository")}
    by_status = {r["status"]: r["c"] for r in conn.execute(
        "SELECT status, COUNT(*) c FROM assertions GROUP BY status")}
    return {"datasets": n, "by_repository": by_repo, "assertion_status_counts": by_status}
