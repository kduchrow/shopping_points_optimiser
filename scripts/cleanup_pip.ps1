# scripts/cleanup_pip.ps1

Write-Host "=== Listing all installed packages ==="
pip list

Write-Host "=== Listing outdated packages ==="
pip list --outdated

Write-Host "=== [Manual Step] Review and uninstall unused packages ==="
Write-Host "Edit requirements.txt or pyproject.toml to remove unused packages, then run:"
Write-Host "pip uninstall <package-name>"
Read-Host "Press Enter to continue after manual cleanup..."

Write-Host "=== Upgrading all outdated packages ==="
pip list --outdated --format=freeze | ForEach-Object {
    $pkg = $_.Split('=')[0]
    pip install --upgrade $pkg
}

Write-Host "=== Freezing current dependencies to requirements.txt ==="
pip freeze | Out-File -Encoding utf8 requirements.txt

Write-Host "=== Running tests to verify everything works ==="
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Please review before proceeding."
    exit 1
}

Write-Host "=== Pip cleanup and update complete! ==="
