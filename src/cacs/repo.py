#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Git repository operations via subprocess."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class RepoManager:
    """Manage a temporary clone of the config repository."""

    def __init__(self, repo_url: str, branch: str = "main"):
        self.repo_url = repo_url
        self.branch = branch
        self._tmp_dir: Optional[Path] = None

    def __enter__(self) -> "RepoManager":
        self.sync()
        return self

    def __exit__(self, *_args: object) -> None:
        self.cleanup()

    def sync(self) -> Path:
        """Clone or pull the repo into a temp directory."""
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="cacs_"))
        self._run_git(
            "clone",
            "--branch",
            self.branch,
            "--single-branch",
            "--depth",
            "1",
            self.repo_url,
            str(self._tmp_dir),
        )
        return self._tmp_dir

    @property
    def path(self) -> Path:
        """Return the temporary repo path."""
        if self._tmp_dir is None:
            raise RuntimeError("Repo not synced yet, call sync() first")
        return self._tmp_dir

    def commit_and_push(self, message: str) -> None:
        """Stage all changes, commit, and push."""
        self._run_git("add", "-A", cwd=self._tmp_dir)
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=self._tmp_dir,
            capture_output=True,
        )
        if result.returncode == 0:
            return  # Nothing to commit
        self._run_git("commit", "-m", message, cwd=self._tmp_dir)
        self._run_git("push", "origin", self.branch, cwd=self._tmp_dir)

    def cleanup(self) -> None:
        """Remove the temporary directory."""
        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir)
            self._tmp_dir = None

    @staticmethod
    def _run_git(
        *args: str,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command and raise on failure."""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
