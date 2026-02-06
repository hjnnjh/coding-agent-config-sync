# cacs - Coding Agent Config Sync

[中文文档](README.md)

A CLI tool for syncing AI coding assistant configurations across Mac/Linux devices. Store configs in a GitHub private repo with pull/push/backup/restore support.

## Supported Tools

- **Claude Code Router (CCR)** - Config file and presets directory
- **OpenCode** - Presets directory
- Extensible to any tool via `sync_config.yaml`

## Installation

```bash
# Clone the project
git clone <repo-url>
cd coding-agent-config-sync

# Install globally
uv run cacs install
```

## Configuration

Edit `~/.config/cacs/sync_config.yaml`:

```yaml
repo: "git@github.com:your-user/your-config-repo.git"
branch: "main"
backup_dir: "~/.config/cacs/backups"
max_backups: 10

items:
  - name: "ccr-config"
    repo_path: "claude-code-router/config.json"
    target_path: "~/.claude-code-router/config.json"
    type: "file"

  - name: "ccr-presets"
    repo_path: "claude-code-router/presets"
    target_path: "~/.claude-code-router/presets"
    type: "directory"
```

Each sync item requires `name`, `repo_path` (path in repo), `target_path` (local path), and `type` (`file` or `directory`).

## Usage

```bash
# First time: upload local configs to repo
cacs init

# Pull remote configs (auto-backup before overwrite)
cacs pull

# Push local configs to remote
cacs push -m "update presets"

# Show diff between local and repo
cacs status

# List all backups
cacs backup list

# Restore from backup (interactive selection)
cacs backup restore

# Restore from a specific backup
cacs backup restore 20250206_120000_pull

# Uninstall
cacs uninstall
```

## Global Options

```bash
# Specify config file path
cacs --config /path/to/sync_config.yaml pull
```

Config lookup order: `--config` > `$CACS_CONFIG` env var > `~/.config/cacs/sync_config.yaml` > project directory.

## Dependencies

- Python >= 3.12
- Git (system-installed)
- [uv](https://docs.astral.sh/uv/) (package manager)

## License

[MIT](LICENSE)
