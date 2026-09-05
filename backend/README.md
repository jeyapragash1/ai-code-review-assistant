# AI-Powered GitHub Code Review Assistant API

Initial FastAPI backend foundation for automated GitHub pull request analysis and code review.

## Requirements

- Python 3.12

## Setup

From the `backend` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

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

## Configuration

Copy `.env.example` to `.env` for local overrides. Do not commit real secrets.
