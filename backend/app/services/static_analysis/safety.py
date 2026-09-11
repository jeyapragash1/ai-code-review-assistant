from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath

from app.core.config import Settings
from app.schemas.github import GitHubPullRequestFile
from app.services.static_analysis.types import AnalysisFile, SkippedFile

DRIVE_PATH_RE = re.compile(r"^[A-Za-z]:")


def normalize_repository_path(value: str) -> str:
    if "\x00" in value or "\\" in value or value.startswith("/") or DRIVE_PATH_RE.match(value):
        raise ValueError("Unsafe repository path")
    path = PurePosixPath(value)
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("Unsafe repository path")
    return path.as_posix()


def should_analyze(metadata: GitHubPullRequestFile, settings: Settings) -> str | None:
    try:
        path = normalize_repository_path(metadata.filename)
    except ValueError:
        return "unsafe_path"
    if metadata.status == "removed":
        return "deleted_file"
    if not path.endswith(".py"):
        return "unsupported_file_type"
    if metadata.patch is not None and len(metadata.patch.encode("utf-8")) > settings.static_review_max_patch_bytes:
        return "patch_too_large"
    return None


def local_path_for(root: Path, repository_path: str) -> Path:
    destination = root.joinpath(*PurePosixPath(repository_path).parts)
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()
    if os.path.commonpath([str(resolved_root), str(resolved_destination)]) != str(resolved_root):
        raise ValueError("Unsafe repository path")
    return destination


def prepare_analysis_file(root: Path, repository_path: str, content: bytes, settings: Settings) -> AnalysisFile:
    if len(content) > settings.static_review_max_file_bytes:
        raise ValueError("file_too_large")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("unsupported_encoding") from exc
    local_path = local_path_for(root, repository_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)
    return AnalysisFile(repository_path=repository_path, local_path=str(local_path), content=content, text=text)


def skipped(path: str, reason: str) -> SkippedFile:
    try:
        path = normalize_repository_path(path)
    except ValueError:
        path = "<unsafe-path>"
    return SkippedFile(path=path, reason=reason)
