# Docker build script with automatic version tagging (PowerShell)
# Usage: .\scripts\docker-build.ps1 [-Push]

param(
    [switch]$Push
)

$ErrorActionPreference = "Stop"

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Extract version from spo/version.py
$VersionFile = Join-Path $ProjectRoot "spo\version.py"
$VersionContent = Get-Content $VersionFile -Raw
if ($VersionContent -match '__version__\s*=\s*["\']([^"\']+)["\']') {
    $AppVersion = $Matches[1]
} else {
    throw "Could not extract version from spo/version.py"
}

# Get git info
try {
    $VcsRef = (git rev-parse --short HEAD 2>$null)
} catch {
    $VcsRef = "unknown"
}

$BuildDate = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Image name
$ImageName = "shopping-points-optimiser"

Write-Host "🏗️  Building Docker image..." -ForegroundColor Cyan
Write-Host "   Version: $AppVersion" -ForegroundColor Gray
Write-Host "   Git Ref: $VcsRef" -ForegroundColor Gray
Write-Host "   Build Date: $BuildDate" -ForegroundColor Gray
Write-Host ""

# Build the image
docker build `
  --build-arg APP_VERSION="$AppVersion" `
  --build-arg BUILD_DATE="$BuildDate" `
  --build-arg VCS_REF="$VcsRef" `
  --build-arg FLASK_ENV="$($env:FLASK_ENV ?? 'production')" `
  -t "${ImageName}:${AppVersion}" `
  -t "${ImageName}:latest" `
  $ProjectRoot

if ($LASTEXITCODE -ne 0) {
    throw "Docker build failed"
}

Write-Host ""
Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "   Tagged as: ${ImageName}:${AppVersion}" -ForegroundColor Gray
Write-Host "   Tagged as: ${ImageName}:latest" -ForegroundColor Gray
Write-Host ""

# Inspect labels
Write-Host "📋 Image metadata:" -ForegroundColor Cyan
$Labels = docker inspect "${ImageName}:${AppVersion}" --format='{{json .Config.Labels}}' | ConvertFrom-Json
$Labels | Format-List

# Push if requested
if ($Push) {
    Write-Host ""
    Write-Host "🚀 Pushing to registry..." -ForegroundColor Cyan
    docker push "${ImageName}:${AppVersion}"
    docker push "${ImageName}:latest"
    Write-Host "✅ Push complete!" -ForegroundColor Green
}
