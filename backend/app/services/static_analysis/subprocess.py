from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class AnalyzerError(Exception):
    """Controlled analyzer failure safe for logs and CLI output."""


class AnalyzerTimeoutError(AnalyzerError):
    pass


@dataclass(frozen=True)
class AnalyzerProcessResult:
    returncode: int
    stdout: str
    stderr: str


def analyzer_environment() -> dict[str, str]:
    keep = ("PATH", "SYSTEMROOT", "COMSPEC", "PATHEXT", "TEMP", "TMP")
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_COLOR"] = "1"
    return env


async def run_analyzer(args: list[str], cwd: Path, timeout_seconds: float) -> AnalyzerProcessResult:
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            args,
            cwd=str(cwd),
            env=analyzer_environment(),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise AnalyzerTimeoutError("Analyzer timed out.") from None
    return AnalyzerProcessResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
