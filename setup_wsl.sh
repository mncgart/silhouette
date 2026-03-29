#!/usr/bin/env bash
set -euo pipefail

# Silhouette WSL2 setup script for Ubuntu 22.04/24.04
# Usage:
#   bash setup_wsl.sh
# Optional env vars:
#   PYTHON_BIN=python3.11 VENV_DIR=.venv

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

info() { printf "\n[setup] %s\n" "$1"; }
warn() { printf "\n[warn] %s\n" "$1"; }

if ! grep -qi microsoft /proc/version 2>/dev/null; then
  warn "This script is intended for WSL2 Ubuntu. Continuing anyway..."
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required." >&2
  exit 1
fi

info "Updating apt package index"
sudo apt update

info "Installing system dependencies (python venv, ffmpeg, build tools)"
sudo apt install -y \
  ffmpeg \
  git \
  curl \
  ca-certificates \
  build-essential \
  pkg-config \
  "$PYTHON_BIN" \
  "${PYTHON_BIN}-venv" \
  "${PYTHON_BIN}-dev"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python binary '$PYTHON_BIN' not found after install." >&2
  exit 1
fi

info "Creating virtual environment at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

info "Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

if [[ ! -f requirements.txt ]]; then
  echo "requirements.txt not found. Run this from repo root." >&2
  exit 1
fi

info "Installing Python dependencies"
pip install -r requirements.txt

if command -v nvidia-smi >/dev/null 2>&1; then
  info "Detected NVIDIA runtime. GPU check:"
  nvidia-smi || true
else
  warn "nvidia-smi not found in WSL. Ensure Windows NVIDIA driver + WSL GPU support are installed."
fi

cat <<'MSG'

Setup completed.

Next steps:
1) Activate environment: source .venv/bin/activate
2) Test run:
   python app.py "AI fitness app for busy professionals" --preset fast-4090 --scenes 3
3) If VRAM issues occur, lower resolution:
   python app.py "Your topic" --width 1024 --height 576 --scenes 3
MSG
