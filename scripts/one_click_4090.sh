#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

log() { printf "\n[ai-studio] %s\n" "$*"; }
warn() { printf "\n[ai-studio][warn] %s\n" "$*"; }

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    return 1
  fi
}

install_apt_packages() {
  if require_cmd apt-get; then
    log "Installing system packages (sudo may prompt for password)..."
    sudo apt-get update
    sudo apt-get install -y \
      python3 python3-venv python3-pip \
      git curl wget ffmpeg build-essential
  else
    warn "apt-get not found. Install python3, venv, pip, git, curl, ffmpeg manually."
  fi
}

check_nvidia() {
  if require_cmd nvidia-smi; then
    log "Detected NVIDIA GPU:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
  else
    warn "nvidia-smi not found. Ensure NVIDIA driver + CUDA runtime are installed."
  fi
}

setup_venv() {
  log "Creating Python virtual environment at ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip wheel setuptools

  log "Installing core Python packages"
  pip install \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  pip install \
    diffusers transformers accelerate xformers bitsandbytes \
    fastapi uvicorn[standard] gradio pydantic redis moviepy
}

install_ollama_optional() {
  if require_cmd ollama; then
    log "ollama already installed."
    return
  fi

  if require_cmd curl; then
    log "Installing ollama (optional local LLM runtime)..."
    curl -fsSL https://ollama.com/install.sh | sh
  else
    warn "curl not found, skipping ollama install."
  fi
}

install_piper_optional() {
  if require_cmd piper; then
    log "piper already installed."
    return
  fi

  if require_cmd apt-get; then
    log "Attempting to install piper (if available in distro repos)..."
    sudo apt-get install -y piper-tts || warn "piper-tts not available in this distro repo; install manually if needed."
  else
    warn "Cannot auto-install piper on this platform."
  fi
}

post_install_notes() {
  cat <<MSG

Setup complete.

Next steps:
1) Activate environment:
   source "${VENV_DIR}/bin/activate"
2) Use model profile:
   ${ROOT_DIR}/config/models.4090.yaml
3) (Optional) Pull LLM model:
   ollama pull qwen2.5:7b-instruct

Tip: start with FLUX.1-schnell + LTX at 720p for smooth iteration.
MSG
}

main() {
  log "Starting one-click laptop setup for AI Studio (no ComfyUI)."
  install_apt_packages
  check_nvidia
  setup_venv
  install_ollama_optional
  install_piper_optional
  post_install_notes
}

main "$@"
