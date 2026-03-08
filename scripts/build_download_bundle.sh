#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUNDLE_DIR="${DIST_DIR}/ai-studio-4090-bundle"
ZIP_PATH="${DIST_DIR}/ai-studio-4090-bundle.zip"

if ! command -v zip >/dev/null 2>&1; then
  echo "zip command not found. Install zip package first." >&2
  exit 1
fi

python3 - <<PY
from pathlib import Path
import shutil

dist = Path(r"${DIST_DIR}")
bundle = Path(r"${BUNDLE_DIR}")
zip_path = Path(r"${ZIP_PATH}")

dist.mkdir(parents=True, exist_ok=True)
if bundle.exists():
    shutil.rmtree(bundle)
if zip_path.exists():
    zip_path.unlink()

(bundle / "config").mkdir(parents=True, exist_ok=True)
(bundle / "docs").mkdir(parents=True, exist_ok=True)
(bundle / "scripts").mkdir(parents=True, exist_ok=True)
(bundle / "requirements").mkdir(parents=True, exist_ok=True)
PY

cp "${ROOT_DIR}/README.md" "${BUNDLE_DIR}/README.md"
cp "${ROOT_DIR}/config/models.4090.yaml" "${BUNDLE_DIR}/config/models.4090.yaml"
cp "${ROOT_DIR}/docs/model_recommendations.md" "${BUNDLE_DIR}/docs/model_recommendations.md"
cp "${ROOT_DIR}/docs/upgrade_blueprint.md" "${BUNDLE_DIR}/docs/upgrade_blueprint.md"
cp "${ROOT_DIR}/scripts/one_click_4090.sh" "${BUNDLE_DIR}/scripts/one_click_4090.sh"
cp "${ROOT_DIR}/requirements/base.txt" "${BUNDLE_DIR}/requirements/base.txt"
cp "${ROOT_DIR}/requirements/cuda121.txt" "${BUNDLE_DIR}/requirements/cuda121.txt"

cat > "${BUNDLE_DIR}/DOWNLOAD_FIRST.md" <<'MSG'
# Download Package: AI Studio 4090 (No ComfyUI)

This folder contains everything needed to start setup on your laptop.

## Quick start
```bash
cd scripts
bash one_click_4090.sh
```

## Included files
- `README.md`
- `config/models.4090.yaml`
- `docs/model_recommendations.md`
- `docs/upgrade_blueprint.md`
- `requirements/base.txt`
- `requirements/cuda121.txt`
- `scripts/one_click_4090.sh`
MSG

(
  cd "${DIST_DIR}"
  zip -r "$(basename "${ZIP_PATH}")" "$(basename "${BUNDLE_DIR}")" >/dev/null
)

if command -v sha256sum >/dev/null 2>&1; then
  (
    cd "${DIST_DIR}"
    sha256sum "$(basename "${ZIP_PATH}")" > "$(basename "${ZIP_PATH}").sha256"
  )
fi

echo "Created: ${ZIP_PATH}"
if [[ -f "${ZIP_PATH}.sha256" ]]; then
  echo "Created: ${ZIP_PATH}.sha256"
fi
