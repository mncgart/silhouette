#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUNDLE_DIR="${DIST_DIR}/ai-studio-4090-bundle"
ZIP_PATH="${DIST_DIR}/ai-studio-4090-bundle.zip"

mkdir -p "${DIST_DIR}"
rm -rf "${BUNDLE_DIR}" "${ZIP_PATH}"
mkdir -p "${BUNDLE_DIR}/config" "${BUNDLE_DIR}/docs" "${BUNDLE_DIR}/scripts"

cp "${ROOT_DIR}/README.md" "${BUNDLE_DIR}/README.md"
cp "${ROOT_DIR}/config/models.4090.yaml" "${BUNDLE_DIR}/config/models.4090.yaml"
cp "${ROOT_DIR}/docs/model_recommendations.md" "${BUNDLE_DIR}/docs/model_recommendations.md"
cp "${ROOT_DIR}/scripts/one_click_4090.sh" "${BUNDLE_DIR}/scripts/one_click_4090.sh"

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
- `scripts/one_click_4090.sh`
MSG

(
  cd "${DIST_DIR}"
  zip -r "$(basename "${ZIP_PATH}")" "$(basename "${BUNDLE_DIR}")" >/dev/null
)

echo "Created: ${ZIP_PATH}"
