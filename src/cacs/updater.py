#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-update support for cacs."""

import json
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click

from cacs import __version__

GITHUB_TAGS_URL = "https://api.github.com/repos/hjnnjh/coding-agent-config-sync/tags"
REPO_DIR = Path.home() / ".local" / "share" / "cacs"
CACHE_FILE = Path.home() / ".config" / "cacs" / ".update_check"
CHECK_INTERVAL = 86400  # 24 hours


@dataclass
class VersionInfo:
    current: str
    latest: str
    has_update: bool


def fetch_latest_version() -> Optional[str]:
    """Fetch latest tag from GitHub API."""
    try:
        req = urllib.request.Request(
            GITHUB_TAGS_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            tags = json.loads(resp.read().decode())
        if not tags:
            return None
        return tags[0]["name"].lstrip("v")
    except Exception:
        return None


def _compare_versions(current: str, latest: str) -> bool:
    """Return True if latest > current."""

    def _to_ints(v: str) -> List[int]:
        return [int(x) for x in v.split(".")]

    return _to_ints(latest) > _to_ints(current)


def check_update() -> Optional[VersionInfo]:
    """Check for available update."""
    latest = fetch_latest_version()
    if latest is None:
        return None
    has_update = _compare_versions(__version__, latest)
    return VersionInfo(
        current=__version__,
        latest=latest,
        has_update=has_update,
    )


def run_update() -> str:
    """Execute update via git pull + uv tool install."""
    result = subprocess.run(
        ["git", "-C", str(REPO_DIR), "pull", "--ff-only"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"git pull failed:\n{result.stderr.strip()}"
    git_msg = result.stdout.strip()
    result = subprocess.run(
        ["uv", "tool", "install", "--force", str(REPO_DIR)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"uv tool install failed:\n{result.stderr.strip()}"
    uv_msg = result.stdout.strip()
    return f"{git_msg}\n{uv_msg}"


def background_check() -> None:
    """Background update check with 24h caching."""
    try:
        now = time.time()
        cache = _read_cache()
        if cache and now - cache.get("last_check", 0) < CHECK_INTERVAL:
            if cache.get("has_update"):
                _print_hint(cache["latest"])
            return
        info = check_update()
        if info is None:
            return
        _write_cache(now, info)
        if info.has_update:
            _print_hint(info.latest)
    except Exception:
        pass


def _read_cache() -> Optional[dict]:
    """Read cached check result."""
    if not CACHE_FILE.exists():
        return None
    return json.loads(CACHE_FILE.read_text())


def _write_cache(ts: float, info: VersionInfo) -> None:
    """Write check result to cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(
            {
                "last_check": ts,
                "latest": info.latest,
                "has_update": info.has_update,
            }
        )
    )


def _print_hint(latest: str) -> None:
    """Print update hint."""
    click.echo(
        f"\nNew version available: {latest} "
        f"(current: {__version__}). "
        f"Run `cacs update install` to upgrade."
    )
