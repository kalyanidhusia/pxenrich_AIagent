# pxEnrich Cancer Evidence

A public-facing AI product that lets non-proteomics users ask ordinary-language
questions about breast-cancer research and get **evidence-linked answers**
grounded in public proteomics datasets (ProteomeXchange / PRIDE / MassIVE) —
with a read-only **MCP server** exposing the same backend to ChatGPT Plugins,
Claude, and any MCP-compatible host.

Built against the *pxEnrich Student AI Product Brief (Jan 2027)*.

```
Public web interface  ──┐
                        ├──►  pxEnrich Evidence API  ──►  evidence index (SQLite)
MCP server (4 tools) ───┘           │                         ▲
                                    ▼                         │
                        evidence + provenance + safety   connectors:
                                                         ProteomeCentral · PRIDE · MassIVE
```

## Core principles (non-negotiable, encoded in code and tests)

* **The LLM is not the database.** Retrieval and normalization are
  deterministic (`pxenrich/extraction.py`); the optional LLM only explains
  retrieved evidence.
* **Every evidence field carries provenance**: source type, URL, supporting
  text, scope, confidence, extractor version.
* **Abstention is a feature.** `unknown`, `mixed`, `conflicting`, and
  `abstained` are first-class statuses. A confident answer without provenance
  is a defect — the benchmark harness exits non-zero on any false assertion.
* **Scope matters.** "The study is about HER2" (`study_focus`) is never
  conflated with "the cohort is HER2-positive" (`dataset` scope).
* **Non-diagnostic.** Every answer carries the clinical boundary notice.

## Quick start

```bash
pip install -r requirements.txt

# 1. Build the index from the bundled seed snapshot (offline, ~5 s)
python -m pxenrich.ingest.run_ingest --seed

# 2. Run the web app  →  http://localhost:8080
python -m pxenrich.api

# 3. Run the MCP server (stdio, for Claude Desktop / MCP Inspector)
python -m pxenrich.mcp_server

#    …or as a remote-capable HTTP server (for ChatGPT plugin wiring)
PXENRICH_MCP_TRANSPORT=streamable-http PXENRICH_MCP_PORT=8765 python -m pxenrich.mcp_server
```

### Live ingest (refresh / extend the index)

```bash
# Discovery via ProteomeCentral, deep metadata via PRIDE, first 50 details:
python -m pxenrich.ingest.run_ingest --query "breast cancer" --details 50

# Add MassIVE direct coverage:
python -m pxenrich.ingest.run_ingest --query "breast cancer" --massive
```

The bundled seed (`data/seed/seed_datasets.json`) is a snapshot of 101 real
ProteomeCentral records (retrieved 2026-10-11; 307 matched the query at that
time) so the product runs and demos **without any network access**. Run the
live ingest to refresh values and extend coverage — seed records are
upserted/replaced by accession.

### Enable the LLM answer layer (optional)

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # or OPENAI_API_KEY
export PXENRICH_LLM_MODEL=claude-sonnet-4-5  # optional override
```

Without a key the product runs in **retrieval-only mode**: identical
retrieval, evidence cards, provenance, and abstention; answers use
deterministic plain-language templates instead of LLM narrative. The LLM
prompt (see `pxenrich/llm.py`) restricts the model to retrieved records,
requires accession citations, and instructs abstention; the template answer
is always preserved alongside for comparison.

## MCP tools (all read-only)

| Tool | Purpose |
|---|---|
| `search_cancer_evidence` | Plain-language question → grounded answer + records (audience: plain / clinician / researcher) |
| `find_proteomics_datasets` | Free-text and/or topic dataset discovery |
| `get_dataset_evidence` | Full evidence record for one accession, with "why (not) this label" explanations |
| `compare_studies` | Field-by-field comparison of 2–6 datasets |

Claude Desktop config example:

```json
{
  "mcpServers": {
    "pxenrich": {
      "command": "python",
      "args": ["-m", "pxenrich.mcp_server"],
      "cwd": "/path/to/pxenrich-product"
    }
  }
}
```

For ChatGPT Plugin submission, deploy the streamable-HTTP variant behind
HTTPS and follow OpenAI's current plugin/MCP submission docs (re-check them
before submitting — see brief §13).

## Tests and benchmark

```bash
python -m unittest discover tests -v     # 16 unit/integration tests
python tests/run_benchmark.py            # extraction benchmark + error taxonomy
```

The benchmark harness scores: accuracy, **false-assertion rate** (the fatal
error class — non-zero fails CI), missed values, correct abstention, and
scope errors. Drop the team's 18-record expert benchmark into
`tests/benchmark/benchmark_records.jsonl` (schema in
`tests/benchmark/benchmark_schema.json`) and it automatically replaces the
bundled example records. Mark final-evaluation records with `"set": "holdout"`
and freeze them before tuning rules.

## Repository layout

```
pxenrich/            core package
  models.py            dataclasses: DatasetRecord, EvidenceAssertion, statuses, scopes
  extraction.py        deterministic ER/PR/HER2/subtype/sample/organism rules
  db.py                SQLite schema + FTS5 search index + tool-call log
  search.py            question parser, topic filters, retrieval
  answer.py            grounded answer composer (3 audience levels)
  llm.py               pluggable Anthropic/OpenAI layer (env-var keys)
  api.py               Flask web API + static frontend server
  mcp_server.py        read-only MCP server (mcp 1.x and 2.x compatible)
  ingest/              ProteomeCentral, PRIDE v3, MassIVE connectors + CLI
frontend/            responsive single-page UI (no build step)
data/seed/           offline seed snapshot of real repository records
tests/               unit tests + benchmark harness + benchmark schema
docs/                architecture, deployment, data provenance
```

## Documentation

* [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, data flow, design decisions
* [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — deploying the demo + MCP endpoint
* [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) — sources, logging, security posture

## Clinical boundary

pxEnrich explains research evidence. It does not diagnose disease, recommend
treatment, interpret personal medical records, or replace clinical care.

## License

MIT — see [LICENSE](LICENSE).
