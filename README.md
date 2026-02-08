# cacs - Coding Agent Config Sync

[English](README_EN.md)

跨 Mac/Linux 设备同步 AI 编程助手配置的命令行工具。通过 GitHub 私有仓库存储配置，支持 pull/push/备份/回滚。

## 支持的工具

- **Claude Code Router (CCR)** - 配置文件与预设目录
- **OpenCode** - 预设目录
- 通过 `sync_config.yaml` 可扩展支持任意工具

## 安装

### 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/hjnnjh/coding-agent-config-sync/main/install.sh | sh
```

### 手动安装

```bash
# 克隆项目
git clone <repo-url>
cd coding-agent-config-sync

# 全局安装
uv run cacs install
```

## 配置

编辑 `~/.config/cacs/sync_config.yaml`：

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

每个同步项需指定 `name`、`repo_path`（仓库内路径）、`target_path`（本地路径）和 `type`（`file` 或 `directory`）。

### ignore_fields（JSON 文件）

对于 JSON 类型的配置文件，可通过 `ignore_fields` 指定同步时忽略的字段（点号分隔路径）。被忽略的字段在 pull 时会保留本地值，在 status 比较时也会跳过。

```yaml
  - name: "ccr-config"
    repo_path: "claude-code-router/config.json"
    target_path: "~/.claude-code-router/config.json"
    type: "file"
    ignore_fields:
      - "mcpServers.filesystem.args"
      - "secretKey"
```

## 使用

```bash
# 首次：将本地配置上传到仓库
cacs init

# 拉取远程配置（自动备份当前配置）
cacs pull

# 推送本地配置到远程
cacs push -m "update presets"

# 查看本地与远程差异
cacs status

# 列出所有备份
cacs backup list

# 从备份恢复（交互式选择）
cacs backup restore

# 从指定备份恢复
cacs backup restore 20250206_120000_pull

# 检查更新
cacs update check

# 安装最新版本
cacs update install

# 卸载
cacs uninstall
```

> 每次运行命令时会自动检查更新（24 小时限频），有新版本时会在输出末尾提示。

## 全局选项

```bash
# 指定配置文件路径
cacs --config /path/to/sync_config.yaml pull
```

配置查找顺序：`--config` > `$CACS_CONFIG` 环境变量 > `~/.config/cacs/sync_config.yaml` > 项目目录。

## 依赖

- Python >= 3.12
- Git（系统已安装）
- [uv](https://docs.astral.sh/uv/)（包管理）

## License

[MIT](LICENSE)
