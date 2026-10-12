"""pxEnrich public web API (Flask).

Endpoints (all read-only):
    GET /api/health
    GET /api/stats
    GET /api/topics
    GET /api/search?q=...&audience=plain|clinician|researcher&topics=a,b&limit=20
    GET /api/datasets/<accession>
    GET /api/datasets/<accession>/explain/<field>
    GET /api/compare?accessions=PXD1,PXD2,...

Also serves the static frontend from ../frontend.

Run:  python -m pxenrich.api            (default port 8080)
      PXENRICH_PORT=5000 python -m pxenrich.api
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request, send_from_directory

from . import db as dbmod
from .answer import compose_answer, explain_label, AUDIENCES
from .models import EVIDENCE_FIELDS
from .search import TOPICS, browse_topic, search

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

app = Flask(__name__, static_folder=None)


def _conn():
    # One connection per request keeps things simple and safe for SQLite.
    return dbmod.connect()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "pxenrich", "version": "0.1.0"})


@app.get("/api/stats")
def stats():
    conn = _conn()
    try:
        return jsonify(dbmod.stats(conn))
    finally:
        conn.close()


@app.get("/api/topics")
def topics():
    conn = _conn()
    try:
        out = []
        for name in TOPICS:
            recs = browse_topic(conn, name, limit=500)
            out.append({"topic": name, "count": len(recs)})
        return jsonify({"topics": out})
    finally:
        conn.close()


@app.get("/api/topics/<topic>")
def topic_datasets(topic: str):
    conn = _conn()
    try:
        try:
            recs = browse_topic(conn, topic, limit=int(request.args.get("limit", 50)))
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        dbmod.log_tool_call(conn, "api", "browse_topic", {"topic": topic}, len(recs))
        return jsonify({"topic": topic,
                        "records": [r.to_dict() for r in recs]})
    finally:
        conn.close()


@app.get("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    audience = request.args.get("audience", "plain")
    if audience not in AUDIENCES:
        audience = "plain"
    topic_arg = [t for t in request.args.get("topics", "").split(",") if t]
    limit = min(int(request.args.get("limit", 20)), 100)
    if not q and not topic_arg:
        return jsonify({"error": "Provide q (a question) and/or topics."}), 400
    conn = _conn()
    try:
        retrieval = search(conn, q, limit=limit, topics=topic_arg)
        answer = compose_answer(q, retrieval, audience)
        dbmod.log_tool_call(conn, "api", "search",
                            {"q": q, "topics": topic_arg, "audience": audience},
                            retrieval["returned"])
        return jsonify({
            "answer": answer,
            "records": [r.to_dict() for r in retrieval["records"]],
            "parsed": retrieval["parsed"],
            "total_matches": retrieval["total_matches"],
        })
    finally:
        conn.close()


@app.get("/api/datasets/<accession>")
def dataset_detail(accession: str):
    conn = _conn()
    try:
        rec = dbmod.get_dataset(conn, accession)
        if not rec:
            return jsonify({"error": f"{accession} not in the index. "
                            "It may exist upstream; try the live ingest."}), 404
        return jsonify(rec.to_dict())
    finally:
        conn.close()


@app.get("/api/datasets/<accession>/explain/<fieldname>")
def explain(accession: str, fieldname: str):
    if fieldname not in EVIDENCE_FIELDS:
        return jsonify({"error": f"Unknown field. Fields: {EVIDENCE_FIELDS}"}), 400
    conn = _conn()
    try:
        rec = dbmod.get_dataset(conn, accession)
        if not rec:
            return jsonify({"error": f"{accession} not in the index."}), 404
        return jsonify(explain_label(rec, fieldname))
    finally:
        conn.close()


@app.get("/api/compare")
def compare():
    accs = [a.strip() for a in request.args.get("accessions", "").split(",") if a.strip()]
    if not 2 <= len(accs) <= 6:
        return jsonify({"error": "Provide 2-6 accessions, comma-separated."}), 400
    conn = _conn()
    try:
        records, missing = [], []
        for a in accs:
            rec = dbmod.get_dataset(conn, a)
            (records if rec else missing).append(rec or a)
        fields_table = {}
        for f in EVIDENCE_FIELDS:
            fields_table[f] = {
                r.accession: next(
                    ({"value": x.value, "status": x.status.value,
                      "scope": x.scope.value, "note": x.note}
                     for x in r.assertions if x.field == f),
                    None)
                for r in records if hasattr(r, "accession")
            }
        dbmod.log_tool_call(conn, "api", "compare", {"accessions": accs}, len(records))
        return jsonify({
            "compared": [r.to_dict(include_assertions=False) for r in records
                         if hasattr(r, "accession")],
            "missing": [m for m in missing if isinstance(m, str)],
            "fields": fields_table,
        })
    finally:
        conn.close()


# ----- static frontend -------------------------------------------------------

@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    full = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")  # SPA fallback


def main() -> None:
    port = int(os.environ.get("PXENRICH_PORT", "8080"))
    app.run(host=os.environ.get("PXENRICH_HOST", "0.0.0.0"), port=port)


if __name__ == "__main__":
    main()
