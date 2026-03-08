param(
    [switch]$SkipSystem,
    [switch]$SkipOptional,
    [switch]$DryRun,
    [string]$VenvDir = ""
)

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
$scriptPath = "scripts/one_click_4090.sh"
$flags = @()

if ($SkipSystem) { $flags += "--skip-system" }
if ($SkipOptional) { $flags += "--skip-optional" }
if ($DryRun) { $flags += "--dry-run" }
if ($VenvDir -ne "") { $flags += "--venv-dir"; $flags += $VenvDir }

if ($runner -eq "wsl") {
    Write-Host "[ai-studio] Running installer through WSL bash..."
    & wsl bash $scriptPath @flags
} else {
    Write-Host "[ai-studio] Running installer through bash..."
    & bash $scriptPath @flags
}
