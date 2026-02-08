#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core sync engine."""

import copy
import filecmp
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cacs.backup import BackupManager
from cacs.config import AppConfig, SyncItem
from cacs.repo import RepoManager


def _is_json_with_ignores(item: SyncItem) -> bool:
    """Check if item is a JSON file with ignore_fields."""
    return (
        item.type == "file"
        and bool(item.ignore_fields)
        and item.repo_path.endswith(".json")
    )


def _remove_fields(
    data: dict[str, Any],
    field_paths: list[str],
) -> dict[str, Any]:
    """Deep-copy data and delete fields specified by dot paths."""
    result = copy.deepcopy(data)
    for path in field_paths:
        keys = path.split(".")
        obj = result
        for key in keys[:-1]:
            if not isinstance(obj, dict) or key not in obj:
                break
            obj = obj[key]
        else:
            if isinstance(obj, dict):
                obj.pop(keys[-1], None)
    return result


def _restore_fields(
    base: dict[str, Any],
    source: dict[str, Any],
    field_paths: list[str],
) -> None:
    """Restore ignored field values from source into base in-place."""
    for path in field_paths:
        keys = path.split(".")
        # Navigate source to get the value
        src_obj: Any = source
        for key in keys[:-1]:
            if not isinstance(src_obj, dict) or key not in src_obj:
                break
            src_obj = src_obj[key]
        else:
            if not isinstance(src_obj, dict) or keys[-1] not in src_obj:
                continue
            # Navigate base, create intermediate dicts if needed
            dst_obj = base
            for k in keys[:-1]:
                if k not in dst_obj or not isinstance(dst_obj[k], dict):
                    dst_obj[k] = {}
                dst_obj = dst_obj[k]
            dst_obj[keys[-1]] = copy.deepcopy(src_obj[keys[-1]])


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
        elif _is_json_with_ignores(item):
            dst.parent.mkdir(parents=True, exist_ok=True)
            src_data = json.loads(src.read_text("utf-8"))
            merged = _remove_fields(src_data, item.ignore_fields)
            if dst.exists():
                dst_data = json.loads(dst.read_text("utf-8"))
                _restore_fields(merged, dst_data, item.ignore_fields)
            dst.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
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
        if _is_json_with_ignores(item):
            repo_data = json.loads(repo_path.read_text("utf-8"))
            local_data = json.loads(local_path.read_text("utf-8"))
            repo_clean = _remove_fields(repo_data, item.ignore_fields)
            local_clean = _remove_fields(local_data, item.ignore_fields)
            if repo_clean == local_clean:
                return "unchanged"
            return "modified"
        if filecmp.cmp(str(repo_path), str(local_path), shallow=False):
            return "unchanged"
        return "modified"
