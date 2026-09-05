# AI-Powered GitHub Code Review Assistant API

FastAPI backend foundation for automated GitHub pull request analysis and code review.

## Requirements

- Python 3.12
- PostgreSQL running locally
- Database: `ai_code_review_db`
- Login role: `ai_code_review_app`

## Setup

From the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Configuration

Create `backend/.env` from `.env.example` and set local values:

```powershell
Copy-Item .env.example .env
```

`DATABASE_URL` should point to the local PostgreSQL database using the `ai_code_review_app` role. Keep `.env` private and never commit real credentials.

## Run

```powershell
python -m uvicorn app.main:app --reload
```

The API documentation is available at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## Test

```powershell
python -m pytest
```

## Database

The backend uses SQLAlchemy 2 async sessions with Psycopg 3. FastAPI disposes database connections during application shutdown.

Alembic is configured for async SQLAlchemy and reads `DATABASE_URL` from the application settings:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "describe change"
```

No application tables or migrations are included yet.

## Health Checks

- `GET /api/v1/health` is a lightweight liveness check and does not require PostgreSQL.
- `GET /api/v1/health/ready` checks PostgreSQL with a safe `SELECT 1` and returns `503` if the database is unavailable.
