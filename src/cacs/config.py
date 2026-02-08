#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration loading and validation."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SyncItem:
    name: str
    repo_path: str
    target_path: str
    type: str = "file"
    ignore_fields: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.target_path = str(Path(self.target_path).expanduser())


@dataclass
class AppConfig:
    repo: str
    branch: str = "main"
    backup_dir: str = "~/.config/cacs/backups"
    max_backups: int = 10
    items: list[SyncItem] = field(default_factory=list)

    def __post_init__(self):
        self.backup_dir = str(Path(self.backup_dir).expanduser())


def _find_config_path(explicit: Optional[str] = None) -> Path:
    """Resolve config file path by priority."""
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("CACS_CONFIG")
    if env:
        return Path(env).expanduser()
    user_cfg = Path("~/.config/cacs/sync_config.yaml").expanduser()
    if user_cfg.exists():
        return user_cfg
    # Fallback: project directory (next to this package's pyproject.toml)
    project_cfg = Path(__file__).resolve().parents[2] / "sync_config.yaml"
    if project_cfg.exists():
        return project_cfg
    return user_cfg  # Default location even if missing


def load_config(path: Optional[str] = None) -> AppConfig:
    """Load and validate sync_config.yaml."""
    cfg_path = _find_config_path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with open(cfg_path) as f:
        raw = yaml.safe_load(f)
    if not raw or not isinstance(raw, dict):
        raise ValueError(f"Invalid config: {cfg_path}")
    if not raw.get("repo"):
        raise ValueError("'repo' is required in config")
    items = [SyncItem(**item) for item in raw.get("items", [])]
    return AppConfig(
        repo=raw["repo"],
        branch=raw.get("branch", "main"),
        backup_dir=raw.get("backup_dir", "~/.config/cacs/backups"),
        max_backups=raw.get("max_backups", 10),
        items=items,
    )
