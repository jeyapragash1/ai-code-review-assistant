"""Validate a deliberately small projection; bodies, diffs, messages and URLs are excluded."""
import re
from datetime import UTC, datetime


def positive_id(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 < value < 2**63 else None


def safe_login(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,99}(?:\[bot\])?", value) else None


def safe_metadata(event_type, payload):
    result = {}
    for key in ("number", "size", "distinct_size"):
        value = positive_id(payload.get(key))
        if value is not None:
            result[key] = value
    if event_type == "push":
        for key in ("before", "after"):
            value = payload.get(key)
            if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value):
                result[key] = value
        for key in ("created", "deleted", "forced"):
            if isinstance(payload.get(key), bool):
                result[key] = payload[key]
        commits = payload.get("commits")
        if isinstance(commits, list):
            result["commit_count"] = len(commits)
    return result


def event_timestamp(payload, fallback):
    # GitHub supplies no timestamp for several event types. Keep received time
    # as the explicit fallback rather than inventing historical activity.
    for key in ("pull_request", "issue", "comment", "review", "repository", "installation"):
        item = payload.get(key)
        if isinstance(item, dict) and isinstance(item.get("updated_at"), str):
            try:
                value = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                if value.tzinfo:
                    return value.astimezone(UTC)
            except ValueError:
                pass
    return fallback
