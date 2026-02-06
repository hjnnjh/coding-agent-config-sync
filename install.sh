#!/bin/sh
# cacs installer - https://github.com/hjnnjh/coding-agent-config-sync
set -eu

REPO_URL="https://github.com/hjnnjh/coding-agent-config-sync.git"
INSTALL_DIR="${HOME}/.local/share/cacs"
CONFIG_DIR="${HOME}/.config/cacs"
CONFIG_FILE="${CONFIG_DIR}/sync_config.yaml"

info() { printf '\033[1;34m%s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m%s\033[0m\n' "$*"; }
error() { printf '\033[1;31m%s\033[0m\n' "$*" >&2; exit 1; }

# Check dependencies
command -v git >/dev/null 2>&1 || error "git is required. Install it from https://git-scm.com/"
command -v uv >/dev/null 2>&1 || error "uv is required. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"

# Clone or update
if [ -d "${INSTALL_DIR}/.git" ]; then
    info "Updating existing installation..."
    git -C "${INSTALL_DIR}" pull --ff-only
else
    info "Cloning cacs..."
    rm -rf "${INSTALL_DIR}"
    git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

# Install via uv
info "Installing cacs..."
uv tool install --force "${INSTALL_DIR}"

# Copy default config if not exists
if [ ! -f "${CONFIG_FILE}" ]; then
    mkdir -p "${CONFIG_DIR}"
    cp "${INSTALL_DIR}/sync_config.yaml" "${CONFIG_FILE}"
    info "Default config copied to ${CONFIG_FILE}"
fi

info "Done! cacs installed successfully."
warn "Edit ${CONFIG_FILE} to set your private repo URL."
