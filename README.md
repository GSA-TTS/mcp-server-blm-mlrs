# mcp-server-blm-mlrs

An [MCP](https://modelcontextprotocol.io) server for the BLM MLRS **Geothermal Leases** dataset.

It exposes tools that query the U.S. Bureau of Land Management (BLM) Mineral & Land Records System (MLRS) geothermal leases ArcGIS FeatureServer and returns clean, structured lease data to any MCP client (Claude Desktop, etc.).

## Data source

BLM National MLRS Geothermal Leases FeatureServer:

```
https://gis.blm.gov/nlsdb/rest/services/HUB/BLM_Natl_MLRS_Geothermal_Leases/FeatureServer/0
```

## Tools

### `get_lease_details(case_number)`

Retrieve full details for a single lease by its BLM case serial number.

- **`case_number`** — BLM case serial number, e.g. `'NVNV105806473'`.

Returns a dict of lease details (case name, type, status, state, acreage, commodity, formation, production status, effective/expiration/sale dates, data source), or an `error` message if not found.

### `search_leases(state, status, effective_date_from, effective_date_to, expiration_date_from, expiration_date_to)`

Search leases with optional filters. All parameters are optional; if none are given, all leases are returned (capped at 50 records).

| Parameter | Field | Description |
|---|---|---|
| `state` | `ADMIN_STATE` | Two-letter admin state code, e.g. `'NV'` |
| `status` | `CSE_DISP` | Case disposition/status, e.g. `'Authorized'` |
| `effective_date_from` | `EFF_DT` | Inclusive lower bound, ISO date `'YYYY-MM-DD'` |
| `effective_date_to` | `EFF_DT` | Inclusive upper bound, ISO date `'YYYY-MM-DD'` |
| `expiration_date_from` | `EXP_DT` | Inclusive lower bound, ISO date `'YYYY-MM-DD'` |
| `expiration_date_to` | `EXP_DT` | Inclusive upper bound, ISO date `'YYYY-MM-DD'` |

Returns `{"count": <int>, "leases": [ {lease summary}, ... ]}`, or an `error` message on failure.

## Installation

Requires Python >= 3.11.

```bash
uv sync
```

## Running

By default the server runs over **stdio**, suitable for local MCP clients:

```bash
uv run python -m geothermal_leases.app
```

If a `PORT` (or `DATABRICKS_APP_PORT`) environment variable is set, it instead serves over **HTTP** on that port:

```bash
PORT=8000 uv run python -m geothermal_leases.app
```

A health check is available at `GET /health` when running over HTTP.

## Configuring an MCP client

Example entry for a client that launches MCP servers over stdio:

```json
{
  "mcpServers": {
    "geothermal-leases": {
      "command": "uv",
      "args": ["run", "python", "-m", "geothermal_leases.app"],
      "cwd": "/path/to/mcp-server-blm-mlrs"
    }
  }
}
```

## Project layout

```
src/geothermal_leases/
├── app.py                       # FastMCP server entrypoint (stdio / HTTP)
├── routes.py                    # Custom HTTP routes (health check)
└── tools/
    ├── __init__.py              # Tool registration
    ├── _blm.py                  # Shared BASE_URL + date helpers
    ├── get_lease_details.py     # get_lease_details tool
    └── search_leases.py         # search_leases tool
```
