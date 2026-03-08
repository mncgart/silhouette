$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "scripts\one_click_4090.ps1"
if (-not (Test-Path $script)) {
    throw "Missing file: scripts\one_click_4090.ps1. Ensure you downloaded the full project (not partial files)."
}

& $script @args
