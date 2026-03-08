$ErrorActionPreference = "Stop"

function Get-BashRunner {
    if (Get-Command wsl -ErrorAction SilentlyContinue) {
        return "wsl"
    }
    if (Get-Command bash -ErrorAction SilentlyContinue) {
        return "bash"
    }
    throw "Neither 'wsl' nor 'bash' was found. Install WSL (recommended) or Git Bash."
}

$runner = Get-BashRunner
$scriptPath = "scripts/build_download_bundle.sh"

if ($runner -eq "wsl") {
    Write-Host "[ai-studio] Building zip through WSL bash..."
    & wsl bash $scriptPath
} else {
    Write-Host "[ai-studio] Building zip through bash..."
    & bash $scriptPath
}
