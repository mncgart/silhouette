#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_VENV_DIR="${ROOT_DIR}/.venv"
VENV_DIR="${DEFAULT_VENV_DIR}"
INSTALL_SYSTEM_PACKAGES=1
INSTALL_OPTIONAL_TOOLS=1
DRY_RUN=0

log() { printf "\n[ai-studio] %s\n" "$*"; }
warn() { printf "\n[ai-studio][warn] %s\n" "$*"; }

usage() {
  cat <<MSG
Usage: bash scripts/one_click_4090.sh [options]

Options:
  --venv-dir <path>      Custom venv path (default: .venv)
  --skip-system          Skip apt-based system package installation
  --skip-optional        Skip optional ollama/piper installation
  --dry-run              Print planned actions without executing installs
  -h, --help             Show this help
MSG
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf "[dry-run] %s\n" "$*"
  else
    eval "$*"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --venv-dir)
        if [[ $# -lt 2 ]]; then
          echo "Missing value for --venv-dir" >&2
          exit 1
        fi
        VENV_DIR="$2"
        shift 2
        ;;
      --skip-system)
        INSTALL_SYSTEM_PACKAGES=0
        shift
        ;;
      --skip-optional)
        INSTALL_OPTIONAL_TOOLS=0
        shift
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage
        exit 1
        ;;
    esac
  done
}

check_minimum_requirements() {
  if ! require_cmd python3; then
    echo "python3 is required but not installed." >&2
    exit 1
  fi

  local py_version
  py_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  log "Detected Python ${py_version}"

  if ! require_cmd git; then
    warn "git not found; install git for model/project workflows."
  fi
}

install_apt_packages() {
  if [[ "$INSTALL_SYSTEM_PACKAGES" -eq 0 ]]; then
    log "Skipping system package installation (--skip-system)."
    return
  fi

  if require_cmd apt-get; then
    if require_cmd sudo; then
      log "Installing system packages via apt-get..."
      run_cmd "sudo apt-get update"
      run_cmd "sudo apt-get install -y python3 python3-venv python3-pip git curl wget ffmpeg build-essential"
    else
      warn "sudo not found; skipping apt installation. Install prerequisites manually."
    fi
  else
    warn "apt-get not found. Install python3, venv, pip, git, curl, ffmpeg manually."
  fi
}

check_nvidia() {
  if require_cmd nvidia-smi; then
    log "Detected NVIDIA GPU:"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      printf "[dry-run] nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader\n"
    else
      nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
    fi
  else
    warn "nvidia-smi not found. Ensure NVIDIA driver + CUDA runtime are installed."
  fi
}

setup_venv() {
  log "Creating virtual environment at ${VENV_DIR}"
  run_cmd "python3 -m venv '${VENV_DIR}'"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf "[dry-run] source '%s/bin/activate'\n" "$VENV_DIR"
    printf "[dry-run] python -m pip install --upgrade pip wheel setuptools\n"
    printf "[dry-run] pip install -r requirements/cuda121.txt -r requirements/base.txt\n"
    return
  fi

  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip wheel setuptools

  log "Installing Python dependencies"
  pip install -r "${ROOT_DIR}/requirements/cuda121.txt" -r "${ROOT_DIR}/requirements/base.txt"
}

install_ollama_optional() {
  if [[ "$INSTALL_OPTIONAL_TOOLS" -eq 0 ]]; then
    log "Skipping optional ollama install (--skip-optional)."
    return
  fi

  if require_cmd ollama; then
    log "ollama already installed."
    return
  fi

  if require_cmd curl; then
    log "Installing ollama (optional local LLM runtime)..."
    run_cmd "curl -fsSL https://ollama.com/install.sh | sh"
  else
    warn "curl not found, skipping ollama install."
  fi
}

install_piper_optional() {
  if [[ "$INSTALL_OPTIONAL_TOOLS" -eq 0 ]]; then
    log "Skipping optional piper install (--skip-optional)."
    return
  fi

  if require_cmd piper; then
    log "piper already installed."
    return
  fi

  if require_cmd apt-get && require_cmd sudo; then
    log "Attempting to install piper (if available in distro repos)..."
    if [[ "$DRY_RUN" -eq 1 ]]; then
      printf "[dry-run] sudo apt-get install -y piper-tts\n"
    else
      sudo apt-get install -y piper-tts || warn "piper-tts not available in this distro repo; install manually if needed."
    fi
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
  parse_args "$@"
  log "Starting one-click laptop setup for AI Studio (no ComfyUI)."
  check_minimum_requirements
  install_apt_packages
  check_nvidia
  setup_venv
  install_ollama_optional
  install_piper_optional
  post_install_notes
}

main "$@"
