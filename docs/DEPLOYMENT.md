# Deployment

## What needs to be publicly reachable

| Service | Process | Default port | Needed for |
|---|---|---|---|
| Web app + API | `python -m pxenrich.api` | 8080 | public demo (brief §10) |
| MCP server (HTTP) | `PXENRICH_MCP_TRANSPORT=streamable-http python -m pxenrich.mcp_server` | 8765 | ChatGPT plugin / remote MCP hosts |

Both read the same SQLite file (`PXENRICH_DB`, default `data/pxenrich.db`).
Read-only workloads share SQLite safely; rebuild the index with the ingest CLI
during a maintenance window or write to a fresh file and swap.

## Minimal production hardening (before the public URL)

1. Put both services behind a reverse proxy with TLS (Caddy or nginx;
   Caddy gives automatic HTTPS). MCP plugin review requires HTTPS.
2. Run Flask under a real server: `pip install gunicorn`,
   `gunicorn -w 2 -b 127.0.0.1:8080 pxenrich.api:app`.
3. Add basic rate limiting at the proxy (the API is read-only, so the risk is
   abuse/load, not data integrity).
4. Set `PXENRICH_NO_LLM=1` on any deployment that should never call an
   external model, or set the API key as a secret, never in code.
5. Schedule `python -m pxenrich.ingest.run_ingest --query "breast cancer"
   --details 100` (cron/systemd timer, weekly) to keep the index fresh.

## Free-tier options that fit this stack

* **Render / Fly.io / Railway** — one small instance runs both processes; add
  a persistent volume for the SQLite file.
* **Hugging Face Spaces** (Gradio-free, Docker space) — fine for the demo URL.
* **University VM / NRP** — National Research Platform works for the demo and
  gives the team room for later reprocessing experiments.

A `Dockerfile` this simple suffices:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
RUN python -m pxenrich.ingest.run_ingest --seed
EXPOSE 8080 8765
CMD ["sh", "-c", "PXENRICH_MCP_TRANSPORT=streamable-http python -m pxenrich.mcp_server & gunicorn -w 2 -b 0.0.0.0:8080 pxenrich.api:app"]
```

## ChatGPT plugin path (brief §2, §8.11)

1. Deploy the streamable-HTTP MCP server behind HTTPS.
2. Verify with MCP Inspector: `npx @modelcontextprotocol/inspector`.
3. Connect it as a personal/test integration where account access permits.
4. Prepare the submission package against OpenAI's **current** plugin docs
   (they change; re-check the pages listed in brief §13 before submitting).
5. Treat directory approval timing as external — the validated endpoint plus
   the documented package is the January deliverable; approval is not.
