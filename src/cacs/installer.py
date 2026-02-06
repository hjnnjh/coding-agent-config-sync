#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install and uninstall cacs as a global command."""

import shutil
import subprocess
from pathlib import Path

import click

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "sync_config.yaml"
USER_CONFIG_DIR = Path("~/.config/cacs").expanduser()


def install() -> None:
    """Install cacs globally via uv tool install."""
    project_dir = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["uv", "tool", "install", str(project_dir)],
        check=True,
    )
    # Copy default config if user config doesn't exist
    user_cfg = USER_CONFIG_DIR / "sync_config.yaml"
    if not user_cfg.exists() and DEFAULT_CONFIG.exists():
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DEFAULT_CONFIG, user_cfg)
        click.echo(f"Config copied to {user_cfg}")
    click.echo("Installed successfully.")


def uninstall() -> None:
    """Uninstall cacs global command."""
    subprocess.run(
        ["uv", "tool", "uninstall", "cacs"],
        check=True,
    )
    click.echo("Uninstalled successfully.")
