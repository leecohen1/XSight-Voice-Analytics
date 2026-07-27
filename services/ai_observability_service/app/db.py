"""SQLite connection and schema initialization.

Plain stdlib `sqlite3` — no ORM, matching the rest of this repository's
"no unnecessary abstraction" convention. `check_same_thread=False` because
FastAPI runs a plain (non-async) `Depends` generator in a worker thread
pool while the `async def` endpoint that consumes it runs on the main
event loop thread — see get_connection()'s docstring.

Monetary values are stored as TEXT (a canonical `Decimal`-parseable
string), never REAL/FLOAT.

**Architecture note (Langfuse adoption):** this schema previously included
a `usage_events` table storing raw per-event token/cost/latency data. That
table has been removed — Langfuse now owns that telemetry (traces,
observations, generations, measured usage, cost) as the single source of
truth; see `app/trace_recorder.py` and the service README's "Architecture
decision" section for the full reasoning. `pricing_config` and
`infrastructure_cost_config` remain unchanged: Langfuse has no equivalent
for either (pricing_config still computes the cost_details this service
sends *to* Langfuse; infrastructure_cost_config has no Langfuse concept at
all — Langfuse only knows about per-generation cost, never fixed monthly
infrastructure spend).
"""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS pricing_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    service TEXT NOT NULL,
    model TEXT,
    billing_unit TEXT NOT NULL,
    input_price TEXT,
    output_price TEXT,
    unit_price TEXT,
    currency TEXT NOT NULL DEFAULT 'USD',
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_reference TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_pricing_config_lookup
    ON pricing_config (provider, service, model, is_active);

CREATE TABLE IF NOT EXISTS infrastructure_cost_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    service TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    monthly_cost_usd TEXT NOT NULL,
    allocation_method TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    """Opens a new connection to the given SQLite file, creating the parent
    directory and the schema if they don't exist yet. Row factory is set to
    `sqlite3.Row` so callers can access columns by name.

    `check_same_thread=False`: FastAPI runs a plain (non-async) `Depends`
    generator like `get_db()` in a worker thread pool, while the `async def`
    endpoint that consumes its yielded connection runs on the main event
    loop thread — two different threads for what is still logically one
    request. Each request already gets its own fresh connection (opened and
    closed within that single request's dependency lifetime), so relaxing
    sqlite3's same-thread check here does not introduce any real
    cross-request connection sharing — it only permits the
    setup-thread/use-thread mismatch FastAPI's own dependency model creates.
    """
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
