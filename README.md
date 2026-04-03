# Finance Dashboard API

Backend for a finance dashboard: **users and roles**, **financial records (CRUD + filters + search + stats)**, **aggregated dashboard APIs**, **analytics and period comparison**, **JWT authentication**, and **role-based access control** enforced on the server.

Stack: **Python 3.11+**, **FastAPI**, **SQLAlchemy 2**, **SQLite** (file-based persistence), **Pydantic v2**.

## Assumptions

- **Single-tenant dataset**: All non-deleted financial records contribute to dashboard aggregates (totals, trends, category breakdown, recent activity). There is no per-user data partitioning for analytics in this version.
- **Roles** (enum `viewer` | `analyst` | `admin`):
  - **Viewer**: Read-only access to **dashboard** and **role metadata** (`/api/meta/roles`). No raw record APIs, search, stats, or analytics.
  - **Analyst**: Viewer capabilities plus **read** access to financial records (list, get, search, stats) and **analytics** endpoints.
  - **Admin**: Full **CRUD** on records and **user management** (create/list/update/delete users). Only admins may create, update, or soft-delete records. Admins cannot delete themselves; users who have created financial records cannot be deleted until those associations are resolved (see error message).
- **Soft delete**: `DELETE /api/records/{id}` sets `deleted_at`; deleted rows are excluded from queries and summaries.
- **Auth**: JWT bearer tokens issued by `POST /api/auth/login`. Passwords are hashed with **pbkdf2_sha256** (via passlib).
- **Bootstrap user**: On first startup (non-test), if the database has no users, a default admin is created: `admin@example.com` / `adminpass123` (change immediately in anything beyond local demo use).

## Setup

```bash
cd "Finance Data Processing and acess control"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL`.

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive docs (Swagger UI)**: http://127.0.0.1:8000/docs  
- **Health**: `GET /health`

## API overview

| Area | Method | Path | Who |
|------|--------|------|-----|
| Auth | POST | `/api/auth/login` | Public |
| Meta | GET | `/api/meta/roles` | Authenticated |
| Users | GET | `/api/users/me` | Authenticated |
| Users | PATCH | `/api/users/me` | Authenticated (self: name/password) |
| Users | POST, GET, GET `/{id}`, PATCH `/{id}`, DELETE `/{id}` | `/api/users` … | **Admin** |
| Records | GET | `/api/records/search` | **Analyst**, **Admin** |
| Records | GET | `/api/records/stats/summary`, `/api/records/stats/by-category` | **Analyst**, **Admin** |
| Records | GET, GET `/{id}` | `/api/records` | **Analyst**, **Admin** |
| Records | POST, PATCH, DELETE | `/api/records` … | **Admin** |
| Dashboard | GET | `/api/dashboard/summary` | **Viewer**, **Analyst**, **Admin** |
| Dashboard | GET | `/api/dashboard/totals`, `/categories`, `/recent`, `/trends` | **Viewer**, **Analyst**, **Admin** |
| Analytics | GET | `/api/analytics/insights`, `/compare-periods`, `/top-categories` | **Analyst**, **Admin** |

**Optional date window** on dashboard and many analytics endpoints: `entry_date_from`, `entry_date_to` (inclusive). Invalid ranges (`from` after `to`) return **400**.

**Listing and search** support `skip`, `limit`; list and search responses include `X-Total-Count`.

**Dashboard** `/summary` returns the full bundle; split endpoints allow fetching only totals, category breakdown, recent rows, or a single trend series (`/trends?granularity=weekly|monthly`).

**Analytics** `/compare-periods` compares income/expense/net between two arbitrary inclusive date ranges. `/top-categories` ranks categories for either `income` or `expense`.

## Tests

```bash
pytest tests -v
```

Tests set `FINANCE_API_TEST=1` so application startup does not touch the default SQLite file or seed the demo admin.

## Tradeoffs

- SQLite keeps local setup simple; production would typically use PostgreSQL and migrations (e.g. Alembic).
- Trend and comparison logic is layered on shared query helpers (`app/services/query_helpers.py`) and dashboard services; very large datasets may need more SQL-side aggregation.
- Rate limiting and refresh tokens are not implemented; JWT expiry is configurable via settings.
