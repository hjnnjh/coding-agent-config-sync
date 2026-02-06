#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backup and restore management."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from cacs.config import AppConfig, SyncItem


@dataclass
class BackupInfo:
    backup_id: str
    path: Path
    timestamp: datetime
    operation: str


class BackupManager:
    """Manage config backups."""

    def __init__(self, config: AppConfig):
        self.backup_dir = Path(config.backup_dir)
        self.max_backups = config.max_backups
        self.items = config.items

    def create(
        self,
        items: list[SyncItem],
        operation: str,
    ) -> Optional[str]:
        """Backup current local configs. Return backup_id or None."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{ts}_{operation}"
        backup_path = self.backup_dir / backup_id
        has_content = False
        for item in items:
            src = Path(item.target_path)
            if not src.exists():
                continue
            dst = backup_path / item.name
            if item.type == "directory":
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            has_content = True
        if not has_content:
            return None
        self._prune()
        return backup_id

    def list_backups(self) -> list[BackupInfo]:
        """List all available backups, newest first."""
        if not self.backup_dir.exists():
            return []
        result: list[BackupInfo] = []
        for entry in sorted(self.backup_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue
            parts = entry.name.split("_", 2)
            if len(parts) < 3:
                continue
            ts_str = f"{parts[0]}_{parts[1]}"
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            operation = parts[2] if len(parts) > 2 else "unknown"
            result.append(
                BackupInfo(
                    backup_id=entry.name,
                    path=entry,
                    timestamp=ts,
                    operation=operation,
                )
            )
        return result

    def restore(self, backup_id: str) -> None:
        """Restore from a backup. Creates safety backup first."""
        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        # Safety net: backup current state before restoring
        self.create(self.items, "pre_restore")
        for item in self.items:
            src = backup_path / item.name
            if not src.exists():
                continue
            dst = Path(item.target_path)
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            if item.type == "directory":
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def _prune(self) -> None:
        """Remove oldest backups exceeding max_backups."""
        backups = self.list_backups()
        if len(backups) <= self.max_backups:
            return
        for old in backups[self.max_backups :]:
            shutil.rmtree(old.path)
