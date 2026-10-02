"""Hermetic defaults: automated tests must never inherit local credentials."""
import os

for name, value in {
    "DEBUG": "false", "APP_ENV": "development", "AUTH_COOKIE_SECURE": "false",
    "AUTH_ALLOWED_GITHUB_LOGINS": "jeyapragash1",
    "DATABASE_URL": "postgresql+psycopg://localhost:5432/ai_code_review_test",
    "GITHUB_TOKEN": "", "GITHUB_APP_ID": "", "GITHUB_APP_PRIVATE_KEY_PATH": "",
    "GITHUB_WEBHOOK_SECRET": "", "GITHUB_APP_CLIENT_ID": "",
    "GITHUB_APP_CLIENT_SECRET": "", "GEMINI_API_KEY": "",
}.items():
    os.environ[name] = value
