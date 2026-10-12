# Data provenance and security posture

## Sources

| Layer | Source | What is used | What is avoided in v1 |
|---|---|---|---|
| Discovery | ProteomeCentral / ProteomeXchange PROXI API | dataset catalog, repository, species, instrument, publication links | raw-file processing |
| Deep metadata | PRIDE Archive REST v3 | project metadata, files list, SDRF pointers, publication links | bulk .RAW downloads |
| Coverage | MassIVE PROXI | public dataset metadata | large-scale reprocessing |

All data ingested is **public research metadata**. No personal health
information, no patient-level identifiers, no user accounts.

## Provenance chain

Every evidence assertion stores:

* `evidence_text` — the exact (or closely excerpted) text supporting the claim
* `source_type` — title / description / keywords / species_field / sdrf / publication / curator
* `source_url` — link to the public record
* `scope` — dataset / cohort_subset / sample / study_focus
* `confidence` — calibrated per source type (title 0.85, description 0.80, keywords 0.60)
* `extracted_by` — rule version (`rule:v0.1`), LLM model, or curator identity
* `status` — asserted / unknown / mixed / conflicting / abstained / not_evaluable

The seed snapshot (`data/seed/seed_datasets.json`) records its retrieval date
and source API, and every record ingested from it is tagged
`source=seed_snapshot` so refreshed live records are distinguishable.
Seed field values were transcribed through a mediated fetch and should be
refreshed from the live APIs before any production claim depends on them.

## Logging (brief §8.9)

`tool_log` records every API/MCP tool call: timestamp, channel, tool name,
parameters, result count. This is enough to reproduce any answer
(same DB version + same parameters → same deterministic retrieval).
It deliberately stores **no user identity and no free-text beyond the query**,
and queries are about public research, not personal health records. Review
retention policy before public launch (e.g., rotate after 90 days).

## Security posture

* The public API and all MCP tools are **read-only**; there is no write path
  from any user-facing surface (brief §8.10).
* No authentication secrets live in the repo; LLM keys come from env vars.
* Outbound calls go only to the repository APIs listed above and (optionally)
  the configured LLM provider.
* Answers always carry the non-diagnostic notice; the abstention machinery is
  the primary guard against overclaiming (brief §12 "medical overreach",
  "LLM hallucination").
