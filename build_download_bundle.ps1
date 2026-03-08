$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "scripts\build_download_bundle.ps1"
if (-not (Test-Path $script)) {
    throw "Missing file: scripts\build_download_bundle.ps1. Ensure you downloaded the full project (not partial files)."
}

& $script @args
