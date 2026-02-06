#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core sync engine."""

import filecmp
import shutil
from dataclasses import dataclass
from pathlib import Path

from cacs.backup import BackupManager
from cacs.config import AppConfig, SyncItem
from cacs.repo import RepoManager


@dataclass
class DiffItem:
    name: str
    status: str  # "new", "modified", "deleted", "unchanged"


class SyncEngine:
    """Orchestrate pull/push/status/init operations."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.backup_mgr = BackupManager(config)

    def pull(self) -> str:
        """Pull from repo and overwrite local configs."""
        with RepoManager(self.config.repo, self.config.branch) as repo:
            self.backup_mgr.create(self.config.items, "pull")
            count = 0
            for item in self.config.items:
                src = repo.path / item.repo_path
                if not src.exists():
                    continue
                self._copy_item(src, Path(item.target_path), item)
                count += 1
            return f"Pulled {count} item(s)"

    def push(self, message: str = "Update configs") -> str:
        """Push local configs to repo."""
        with RepoManager(self.config.repo, self.config.branch) as repo:
            count = 0
            for item in self.config.items:
                src = Path(item.target_path)
                if not src.exists():
                    continue
                self._copy_item(src, repo.path / item.repo_path, item)
                count += 1
            repo.commit_and_push(message)
            return f"Pushed {count} item(s)"

    def status(self) -> list[DiffItem]:
        """Compare local configs with repo."""
        with RepoManager(self.config.repo, self.config.branch) as repo:
            result: list[DiffItem] = []
            for item in self.config.items:
                repo_src = repo.path / item.repo_path
                local = Path(item.target_path)
                st = self._compare(repo_src, local, item)
                result.append(DiffItem(name=item.name, status=st))
            return result

    def init(self) -> str:
        """Initialize repo with current local configs."""
        return self.push("Initial config upload")

    @staticmethod
    def _copy_item(src: Path, dst: Path, item: SyncItem) -> None:
        """Copy a file or directory from src to dst."""
        if item.type == "directory":
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    @staticmethod
    def _compare(
        repo_path: Path,
        local_path: Path,
        item: SyncItem,
    ) -> str:
        """Compare repo vs local, return status string."""
        repo_exists = repo_path.exists()
        local_exists = local_path.exists()
        if not repo_exists and not local_exists:
            return "unchanged"
        if not repo_exists and local_exists:
            return "new"
        if repo_exists and not local_exists:
            return "deleted"
        if item.type == "directory":
            cmp = filecmp.dircmp(str(repo_path), str(local_path))
            if cmp.left_only or cmp.right_only or cmp.diff_files:
                return "modified"
            return "unchanged"
        if filecmp.cmp(str(repo_path), str(local_path), shallow=False):
            return "unchanged"
        return "modified"
