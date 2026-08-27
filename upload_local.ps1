# Local workspace upload to Modrinth + CurseForge (no GitHub Actions).
# Tokens from env or C:\Users\mahou\NightBeam-Knowledge-Base\secrets\local.env
#
# Usage:
#   .\upload_local.ps1 -Version 1.1.0 -Workspace "1.20.1"
#   .\upload_local.ps1 -Version 1.1.0 -Workspace "26.1.2" -DryRun

param(
    [string]$Version = "1.1.0",
    [string]$Workspace = "26.1.2",
    [switch]$CurseForgeOnly,
    [switch]$ModrinthOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$workspaceDir = Join-Path $root $Workspace
if (-not (Test-Path $workspaceDir)) {
    throw "Workspace not found: $Workspace"
}

$notes = Join-Path $root "The-Fisherman-House-$Version-PatchNotes.md"
if (-not (Test-Path $notes)) { $notes = Join-Path $root "PATCH_NOTES.md" }

$jdkByWorkspace = @{
    "1.20.1" = "C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot"
    "1.21.1" = "C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot"
    "26.1.2" = "C:\Program Files\Eclipse Adoptium\jdk-25.0.4.7-hotspot"
    "26.2"   = "C:\Program Files\Eclipse Adoptium\jdk-25.0.4.7-hotspot"
}
$jdkHome = $jdkByWorkspace[$Workspace]
if (-not $jdkHome -or -not (Test-Path $jdkHome)) {
    throw "No JDK mapping for workspace $Workspace (looked for $jdkHome)"
}
$env:JAVA_HOME = $jdkHome
$env:PATH = "$jdkHome\bin;" + ($env:PATH -replace [regex]::Escape("$jdkHome\bin;"), "")

Write-Host "=== Build The Fisherman House v$Version ($Workspace) [JAVA_HOME=$env:JAVA_HOME] ===" -ForegroundColor Green
Push-Location $workspaceDir
try {
    & ".\gradlew.bat" "build" "--no-daemon"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

$nodeArgs = @(
    "scripts/upload_platforms.mjs",
    "--workspace", $Workspace,
    "--version", $Version,
    "--changelog-file", $notes
)
if ($CurseForgeOnly) { $nodeArgs += "--curseforge-only" }
if ($ModrinthOnly) { $nodeArgs += "--modrinth-only" }
if ($DryRun) { $nodeArgs += "--dry-run" }

Write-Host "=== Local upload The Fisherman House v$Version ($Workspace) ===" -ForegroundColor Green
node @nodeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Verify:" -ForegroundColor Cyan
Write-Host "  https://modrinth.com/mod/the-fisherman-house/versions"
Write-Host "  https://www.curseforge.com/minecraft/mc-mods/the-fisherman-house/files"
