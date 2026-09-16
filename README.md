# Threat Intelligence Platform

A self-hosted TIP: automated multi-source collection across four IOC types
(IP, URL, domain, and all three common hash algorithms), Elasticsearch
storage, a FastAPI backend, and a live SOC-style dashboard with a
region-wise threat map. Everything runs from real, live, public threat
feeds — no API keys, no mock data.

```
┌─────────────┐    ┌───────────────┐    ┌──────────────────┐
│ 4 live feeds │──▶│ collector      │──▶│ Elasticsearch     │
│ (abuse.ch)   │    │ (scheduled)   │    │                    │
└─────────────┘    └───────────────┘    └─────────┬──────────┘
                                                     │
                                          ┌──────────▼──────────┐
                                          │ FastAPI backend      │
                                          └──────────┬──────────┘
                                                     │
                                          ┌──────────▼──────────┐
                                          │ React dashboard      │
                                          └──────────────────────┘
```

## Quickstart

```bash
docker compose up --build
```

- Dashboard: **http://localhost:3000**
- API: **http://localhost:8000** (docs at `/docs`)
- Elasticsearch: **http://localhost:9200**

The collector runs its first pass immediately on startup, then every 15
minutes. Give it a minute after `up` finishes before the dashboard has
data — or click **RUN_COLLECTION_NOW** in the dashboard header to trigger
a pass on demand instead of waiting.

## Real data sources — no API keys

| Source | IOC types | Notes |
|---|---|---|
| [URLhaus](https://urlhaus.abuse.ch/) | URL | Recently reported malicious URLs |
| [ThreatFox](https://threatfox.abuse.ch/) | IP, domain, URL, MD5/SHA1/SHA256 | Malware-family tagged, ships its own confidence score |
| [MalwareBazaar](https://bazaar.abuse.ch/) | MD5, SHA1, SHA256 | Each sample emits all three hashes as separate indicators |
| [Feodo Tracker](https://feodotracker.abuse.ch/) | IP | Known botnet C2 infrastructure; already includes country data |

All four are abuse.ch's public **bulk export** endpoints, not their formal
REST APIs — abuse.ch now gates the REST APIs behind a free `auth.abuse.ch`
account (a real, recent platform change caught and worked around while
building this), but the bulk exports genuinely need nothing.

IP-type indicators (and domains/URLs, via best-effort DNS resolution) are
geolocated through [ip-api.com](https://ip-api.com/)'s free tier — no key,
capped at 45 req/min, so the collector self-throttles to 40/min and reuses
any geo data Elasticsearch already has for an IP rather than re-querying it
every run.

## What this is (and isn't)

A genuine, runnable platform — not a mockup. What's real: live collection
from 4 independent sources, deduplication and scoring across them,
Elasticsearch-backed search and aggregation, and a dashboard that reflects
actual current data.

**Honest limitations, by design, to keep scope truthful:**
- Elasticsearch security is disabled (`xpack.security.enabled=false`) —
  correct for local/dev use, **not** for exposing this beyond your own
  machine without adding auth in front of it.
- The region map plots real lat/lon centroids on a labeled grid rather than
  drawing actual country coastlines — accurate positioning without taking
  on a topojson-atlas dependency and an ISO code-mapping table that would
  be easy to get subtly wrong.
- No retention/cleanup job yet — `TIP_IOC_RETENTION_DAYS` is read but not
  enforced. The index just grows; fine for a demo, not for months of
  unattended production use.
- No authentication on the API or dashboard — anyone who can reach the
  ports can query and trigger collection.

## Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate  # or source .venv/bin/activate
pip install -e ".[dev]"
pytest -v                    # 12 tests, including live network tests
pytest -m "not live" -v      # skip the ones that hit real feeds

# Dashboard
cd dashboard
npm install
npm run dev                  # proxies /api to localhost:8000 — run the backend too
```

## Project layout

```
backend/
  src/tip_backend/
    models.py            # the Indicator schema
    collectors/           # one module per source, each a real HTTP client
    geo.py                # rate-limited IP geolocation + DNS-based domain resolution
    processing.py         # dedupe + confidence/severity scoring
    storage.py             # the only module that speaks Elasticsearch DSL
    pipeline_run.py       # orchestrates one full collection pass
    scheduler.py           # standalone process: runs the pipeline on an interval
    api/                    # FastAPI app + routes
  tests/                  # unit tests + live tests against the real feeds
dashboard/
  src/
    components/           # StatCards, RegionMap, IOCTable, TopList
    pages/Dashboard.jsx
    lib/api.js, countryCentroids.js
docker-compose.yml
```

## License

MIT
