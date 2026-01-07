#!/usr/bin/env pwsh
# Test and Rebuild Script for Shopping Points Optimiser
# This script rebuilds the Docker image, restarts the container, and shows logs

param(
    [switch]$SkipBuild,
    [switch]$CleanStart,
    [int]$LogLines = 40
)

Write-Host "[*] Shopping Points Optimiser - Test and Rebuild" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

if ($CleanStart) {
    Write-Host "[CLEAN] Removing all containers and volumes..." -ForegroundColor Yellow
    docker-compose down -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to stop containers" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

if (-not $SkipBuild) {
    Write-Host "[BUILD] Building Docker image..." -ForegroundColor Cyan
    docker-compose build --no-cache shopping-points
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Build complete" -ForegroundColor Green
    Write-Host ""
}

Write-Host "[START] Starting containers..." -ForegroundColor Cyan
if ($CleanStart) {
    docker-compose up -d
} else {
    # Force recreate to pick up new image
    docker-compose up -d --force-recreate shopping-points
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start containers" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Containers started" -ForegroundColor Green
Write-Host ""

Write-Host "[WAIT] Waiting for initialization (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "[LOGS] Container logs (last $LogLines lines):" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose logs shopping-points --tail=$LogLines

Write-Host ""
Write-Host "[OK] Ready for testing!" -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  - Open app:          http://localhost:5000" -ForegroundColor Gray
Write-Host "  - Run tests:         docker-compose exec -T shopping-points python -m pytest -q" -ForegroundColor Gray
Write-Host "  - View logs:         docker-compose logs shopping-points -f" -ForegroundColor Gray
Write-Host "  - Check status:      docker-compose ps" -ForegroundColor Gray
Write-Host "  - Stop containers:   docker-compose down" -ForegroundColor Gray
Write-Host ""
