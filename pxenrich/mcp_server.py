"""pxEnrich MCP server — read-only tools over the same evidence index.

This is the "second doorway" (brief §2): the same backend the website uses,
exposed through the Model Context Protocol so ChatGPT Plugins, Claude, and any
other MCP-compatible host can call it.

All tools are read-only (brief §8.10). Every tool call is logged to the
tool_log table for reproducibility (brief §8.9) — parameters only, no user
identity, no personal health information.

Run (stdio, for local clients):
    python -m pxenrich.mcp_server

Run (streamable HTTP, for remote hosts / plugin submission):
    PXENRICH_MCP_TRANSPORT=streamable-http PXENRICH_MCP_PORT=8765 \
        python -m pxenrich.mcp_server

Compatible with both mcp 1.x (FastMCP) and mcp 2.x (MCPServer).
"""

from __future__ import annotations

import json
import os

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore

from . import db as dbmod
from .answer import compose_answer, explain_label
from .models import EVIDENCE_FIELDS
from .search import TOPICS, browse_topic, search

INSTRUCTIONS = """pxEnrich connects plain-language questions about breast-cancer
research to the public proteomics record (ProteomeXchange / PRIDE / MassIVE).
Answers are evidence-linked: every claim carries dataset accessions, provenance,
and explicit unknown/mixed/conflicting/abstained states. This service explains
research evidence; it does not diagnose, prognose, or recommend treatment."""

mcp = _Server(
    name="pxenrich_mcp",
    instructions=INSTRUCTIONS,
    version="0.1.0",
)

_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False,
              "idempotentHint": True, "openWorldHint": False}


def _json(obj) -> str:
    return json.dumps(obj, indent=2, default=str)


@mcp.tool(name="search_cancer_evidence", annotations=_READ_ONLY)
def search_cancer_evidence(question: str, audience: str = "plain",
                           limit: int = 10) -> str:
    """Answer a plain-language question about breast-cancer proteomics research.

    Returns an evidence-grounded answer plus the matching public datasets with
    per-field assertions (subtype, ER/PR/HER2 status, sample type, organism
    context), provenance snippets, and source links. The answer explicitly
    reports unknown / mixed / conflicting / abstained states instead of
    guessing. audience is one of: plain, clinician, researcher.
    """
    conn = dbmod.connect()
    try:
        retrieval = search(conn, question, limit=min(limit, 25))
        answer = compose_answer(question, retrieval, audience)
        dbmod.log_tool_call(conn, "mcp", "search_cancer_evidence",
                            {"question": question, "audience": audience},
                            retrieval["returned"])
        return _json({
            "answer": answer,
            "records": [r.to_dict() for r in retrieval["records"]],
        })
    finally:
        conn.close()


@mcp.tool(name="find_proteomics_datasets", annotations=_READ_ONLY)
def find_proteomics_datasets(query: str = "", topic: str = "",
                             limit: int = 20) -> str:
    """Find public breast-cancer proteomics datasets by free text and/or topic.

    topic (optional) is one of: triple-negative, her2, er-positive, luminal,
    tumor-tissue, plasma, blood, urine, cell-line, human-patient, animal-model,
    treatment, pre-post-treatment. Returns normalized dataset records with
    repository, species, instrument, dates, and links to the original public
    records (ProteomeCentral + host repository).
    """
    conn = dbmod.connect()
    try:
        if topic:
            if topic not in TOPICS:
                return _json({"error": f"Unknown topic '{topic}'.",
                              "valid_topics": sorted(TOPICS)})
            recs = browse_topic(conn, topic, limit=min(limit, 50))
            if query:
                q = query.lower()
                recs = [r for r in recs if q in r.searchable_text().lower()]
            result = {"topic": topic, "count": len(recs),
                      "records": [r.to_dict() for r in recs]}
        else:
            retrieval = search(conn, query, limit=min(limit, 50))
            result = {"total_matches": retrieval["total_matches"],
                      "records": [r.to_dict() for r in retrieval["records"]]}
        dbmod.log_tool_call(conn, "mcp", "find_proteomics_datasets",
                            {"query": query, "topic": topic},
                            len(result.get("records", [])))
        return _json(result)
    finally:
        conn.close()


@mcp.tool(name="get_dataset_evidence", annotations=_READ_ONLY)
def get_dataset_evidence(accession: str, explain_field: str = "") -> str:
    """Get the full evidence record for one dataset by ProteomeXchange accession.

    Returns all metadata plus every evidence assertion with its status
    (asserted/unknown/mixed/conflicting/abstained), supporting text, source,
    scope, and confidence. Pass explain_field (e.g. 'subtype' or 'her2_status')
    to also get a human-readable explanation of why that label was or was not
    applied — including why a study cannot be confidently labeled.
    """
    conn = dbmod.connect()
    try:
        rec = dbmod.get_dataset(conn, accession.strip())
        if not rec:
            return _json({"error": f"{accession} is not in the local index.",
                          "hint": "Run the live ingest to extend coverage; the "
                                  "accession may still exist upstream at "
                                  "proteomecentral.proteomexchange.org."})
        out = rec.to_dict()
        if explain_field:
            if explain_field not in EVIDENCE_FIELDS:
                out["explain_error"] = f"Unknown field; valid: {EVIDENCE_FIELDS}"
            else:
                out["explanation"] = explain_label(rec, explain_field)
        dbmod.log_tool_call(conn, "mcp", "get_dataset_evidence",
                            {"accession": accession,
                             "explain_field": explain_field}, 1)
        return _json(out)
    finally:
        conn.close()


@mcp.tool(name="compare_studies", annotations=_READ_ONLY)
def compare_studies(accessions: str) -> str:
    """Compare 2-6 datasets field by field (subtype, ER/PR/HER2, sample type,
    organism context, treatment context).

    accessions: comma-separated ProteomeXchange accessions, e.g.
    "PXD057759,PXD019334". Highlights where evidence differs, where it is
    missing, and where labels were deliberately withheld (abstained).
    """
    conn = dbmod.connect()
    try:
        accs = [a.strip() for a in accessions.split(",") if a.strip()]
        if not 2 <= len(accs) <= 6:
            return _json({"error": "Provide 2-6 comma-separated accessions."})
        records, missing = [], []
        for a in accs:
            rec = dbmod.get_dataset(conn, a)
            (records if rec else missing).append(rec or a)
        table = {}
        for f in EVIDENCE_FIELDS:
            table[f] = {}
            for r in records:
                if not hasattr(r, "accession"):
                    continue
                a = next((x for x in r.assertions if x.field == f), None)
                table[f][r.accession] = (
                    {"value": a.value, "status": a.status.value,
                     "evidence": a.evidence_text, "note": a.note}
                    if a else None)
        dbmod.log_tool_call(conn, "mcp", "compare_studies",
                            {"accessions": accs}, len(records))
        return _json({
            "datasets": [r.to_dict(include_assertions=False)
                         for r in records if hasattr(r, "accession")],
            "not_in_index": [m for m in missing if isinstance(m, str)],
            "field_comparison": table,
        })
    finally:
        conn.close()


def main() -> None:
    transport = os.environ.get("PXENRICH_MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        port = int(os.environ.get("PXENRICH_MCP_PORT", "8765"))
        try:
            mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
        except TypeError:
            # some SDK versions configure host/port via settings instead
            mcp.settings.host = "0.0.0.0"   # type: ignore[attr-defined]
            mcp.settings.port = port        # type: ignore[attr-defined]
            mcp.run(transport="streamable-http")
    else:
        mcp.run()  # stdio


if __name__ == "__main__":
    main()
