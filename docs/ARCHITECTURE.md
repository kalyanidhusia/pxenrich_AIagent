# Architecture

## Components

```
                    ┌─────────────────────────────┐
  patient /         │  frontend/ (static SPA)     │   audience toggle:
  clinician /  ───► │  search · topics · evidence │   plain / clinician /
  researcher        │  cards · receipts           │   researcher
                    └──────────────┬──────────────┘
                                   │ JSON
                    ┌──────────────▼──────────────┐
                    │  pxenrich/api.py (Flask)    │  read-only REST
                    └──────────────┬──────────────┘
                                   │
  ChatGPT /        ┌───────────────▼─────────────┐
  Claude /    ───► │  pxenrich/mcp_server.py     │  4 read-only MCP tools,
  MCP hosts        │  (same functions, 2nd door) │  stdio or streamable-http
                   └───────────────┬─────────────┘
                                   │
            ┌──────────────────────▼───────────────────────┐
            │  search.py  →  answer.py  →  llm.py (opt.)   │
            │  question parsing · retrieval · composition  │
            └──────────────────────┬───────────────────────┘
                                   │
            ┌──────────────────────▼───────────────────────┐
            │  db.py — SQLite evidence index               │
            │  datasets · assertions (provenance) · FTS5   │
            │  tool_log (reproducibility)                  │
            └──────────────────────▲───────────────────────┘
                                   │
            ┌──────────────────────┴───────────────────────┐
            │  ingest/ — connectors, one normalized schema │
            │  proteomecentral.py (PROXI discovery)        │
            │  pride.py (v3 REST, deep metadata, SDRF)     │
            │  massive.py (PROXI)                          │
            │  extraction.py runs at ingest time           │
            └──────────────────────────────────────────────┘
```

## Key design decisions

1. **One normalized schema, many repositories.** Connectors map everything to
   `DatasetRecord`; nothing downstream knows which repository a record came
   from (brief §12 "repository coupling").
2. **Extraction at ingest, not at query time.** Deterministic rules run once
   per record and persist assertions with provenance. Queries are fast,
   reproducible, and auditable; rule upgrades re-run over stored records and
   are diffable via `extracted_by` version tags.
3. **Assertion state machine.** Every evidence field of every record has
   exactly one assertion per extractor version with status
   `asserted | unknown | mixed | conflicting | abstained | not_evaluable`.
   The UI renders these as designed states, not errors.
4. **Scope as a first-class dimension.** `study_focus` vs `dataset` scope
   prevents the classic error of labeling a HER2-pulldown study as a
   HER2-positive cohort.
5. **Web API and MCP share one engine.** `search.py`/`answer.py` are called by
   both doorways, so website and plugin can never drift apart (brief §2).
6. **LLM optional and fenced.** `llm.py` only ever sees retrieved records; the
   template answer and records are preserved regardless, so the UI can always
   fall back and evaluations can compare narrative vs. template.
7. **SQLite now, Postgres later.** Plain-SQL schema, no ORM; the swap is a
   connection-string refactor when multi-writer deployment is needed.

## Where students plug in next (maps to brief roles)

* **Data/API engineer** — SDRF download + per-sample parsing
  (`pride.get_sdrf_sample_metadata` returns the file list already); scheduled
  sync; iProX/jPOST direct connectors.
* **AI/MCP engineer** — LLM query-understanding fallback for questions the
  rule parser misses; retrieval re-ranking; richer `compare_studies` output;
  plugin packaging/submission.
* **Frontend/UX** — study drill-down page, saved searches, filters UI,
  accessibility audit, PWA wrapper (stretch).
* **Evaluation/QA** — port the 18-record expert benchmark, freeze the holdout,
  add telemetry dashboards over `tool_log`, latency tracking.
