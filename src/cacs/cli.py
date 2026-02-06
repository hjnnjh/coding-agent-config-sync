#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI entry point using click."""

from typing import Optional

import click

from cacs.config import load_config
from cacs.sync import SyncEngine


@click.group()
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(),
    help="Path to sync_config.yaml",
)
@click.pass_context
def main(ctx: click.Context, config_path: Optional[str]) -> None:
    """Coding Agent Config Sync."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


def _get_engine(ctx: click.Context) -> SyncEngine:
    """Load config and create SyncEngine from context."""
    cfg = load_config(ctx.obj["config_path"])
    return SyncEngine(cfg)


@main.command()
@click.pass_context
def pull(ctx: click.Context) -> None:
    """Pull configs from repo (auto-backup)."""
    engine = _get_engine(ctx)
    result = engine.pull()
    click.echo(result)


@main.command()
@click.option("-m", "--message", default="Update configs")
@click.pass_context
def push(ctx: click.Context, message: str) -> None:
    """Push local configs to repo."""
    engine = _get_engine(ctx)
    result = engine.push(message)
    click.echo(result)


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show diff between local and repo."""
    engine = _get_engine(ctx)
    diffs = engine.status()
    for d in diffs:
        click.echo(f"  {d.status:<12} {d.name}")


@main.command(name="init")
@click.pass_context
def init_cmd(ctx: click.Context) -> None:
    """Initialize repo with current local configs."""
    engine = _get_engine(ctx)
    result = engine.init()
    click.echo(result)


@main.group()
def backup() -> None:
    """Backup management."""


@backup.command(name="list")
@click.pass_context
def backup_list(ctx: click.Context) -> None:
    """List all backups."""
    cfg = load_config(ctx.obj["config_path"])
    from cacs.backup import BackupManager

    mgr = BackupManager(cfg)
    backups = mgr.list_backups()
    if not backups:
        click.echo("No backups found.")
        return
    for b in backups:
        ts = b.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"  {b.backup_id}  ({ts})  [{b.operation}]")


@backup.command(name="restore")
@click.argument("backup_id", required=False)
@click.pass_context
def backup_restore(
    ctx: click.Context,
    backup_id: Optional[str],
) -> None:
    """Restore from a backup."""
    cfg = load_config(ctx.obj["config_path"])
    from cacs.backup import BackupManager

    mgr = BackupManager(cfg)
    if not backup_id:
        backups = mgr.list_backups()
        if not backups:
            click.echo("No backups found.")
            return
        click.echo("Available backups:")
        for i, b in enumerate(backups):
            ts = b.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"  [{i}] {b.backup_id}  ({ts})")
        idx = click.prompt("Select backup", type=int)
        if idx < 0 or idx >= len(backups):
            click.echo("Invalid selection.")
            return
        backup_id = backups[idx].backup_id
    mgr.restore(str(backup_id))
    click.echo(f"Restored from {backup_id}")


@main.command()
def install() -> None:
    """Install cacs as a global command."""
    from cacs.installer import install as do_install

    do_install()


@main.command()
def uninstall() -> None:
    """Uninstall cacs global command."""
    from cacs.installer import uninstall as do_uninstall

    do_uninstall()
