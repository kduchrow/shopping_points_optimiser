#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Synchronizes legal page environment variables from .env to GitHub Secrets
.DESCRIPTION
    Reads IMPRINT_* and PRIVACY_* variables from .env file and sets them as GitHub repository secrets.
    Requires GitHub CLI (gh) to be installed and authenticated.
.EXAMPLE
    .\sync_secrets_to_github.ps1
#>

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed. Please install it from: https://cli.github.com/"
    Write-Host "Windows: winget install --id GitHub.cli" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not authenticated with GitHub CLI. Please run: gh auth login"
    exit 1
}

# Get repository info
$repoInfo = gh repo view --json nameWithOwner -q .nameWithOwner 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not determine repository. Are you in a git repository?"
    exit 1
}

Write-Host "Repository: $repoInfo" -ForegroundColor Cyan
Write-Host ""

# Read .env file
$envFile = Join-Path -Path $PSScriptRoot -ChildPath ".." | Join-Path -ChildPath ".env"
if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at: $envFile"
    exit 1
}

Write-Host "Reading .env file..." -ForegroundColor Green

# Parse .env and filter legal page variables
$secrets = @{}
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    # Skip comments and empty lines
    if ($line -and -not $line.StartsWith("#")) {
        if ($line -match '^(IMPRINT_|PRIVACY_)([A-Z_]+)=(.*)$') {
            $key = $matches[1] + $matches[2]
            $value = $matches[3]

            # Remove quotes if present
            $value = $value -replace '^"(.*)"$', '$1'
            $value = $value -replace "^'(.*)'$", '$1'

            # Only add non-empty values
            if ($value) {
                $secrets[$key] = $value
            }
        }
    }
}

if ($secrets.Count -eq 0) {
    Write-Warning "No IMPRINT_* or PRIVACY_* variables found in .env file"
    exit 0
}

Write-Host "Found $($secrets.Count) legal page variables" -ForegroundColor Green
Write-Host ""

# Confirm before proceeding
Write-Host "The following secrets will be set in GitHub repository:" -ForegroundColor Yellow
$secrets.Keys | Sort-Object | ForEach-Object {
    $valuePreview = if ($secrets[$_].Length -gt 40) {
        $secrets[$_].Substring(0, 37) + "..."
    } else {
        $secrets[$_]
    }
    Write-Host "  - $_" -NoNewline -ForegroundColor Cyan
    Write-Host " = $valuePreview" -ForegroundColor Gray
}
Write-Host ""

$confirmation = Read-Host "Continue? (y/n)"
if ($confirmation -ne 'y') {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Set secrets
Write-Host ""
Write-Host "Setting GitHub secrets..." -ForegroundColor Green
$successCount = 0
$failCount = 0

foreach ($key in $secrets.Keys | Sort-Object) {
    Write-Host "  Setting $key..." -NoNewline

    # Use gh secret set command with piped input
    $secrets[$key] | gh secret set $key 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
if ($failCount -eq 0) {
    Write-Host "Done! Success: $successCount, Failed: $failCount" -ForegroundColor Green
} else {
    Write-Host "Done! Success: $successCount, Failed: $failCount" -ForegroundColor Yellow
}

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "Secrets have been set. Your next deployment will use these values." -ForegroundColor Cyan
}
