# PowerShell script to clean Python environment and restart Docker containers
# Save as cleanup_and_restart.ps1 and run in your project root

Write-Host "Cleaning __pycache__ folders..."
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Write-Host "✅ Removed all __pycache__ folders."

Write-Host "Cleaning .pyc files..."
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force
Write-Host "✅ Removed all .pyc files."

Write-Host "Restarting Docker containers..."
docker compose down
Start-Sleep -Seconds 2
docker compose up -d
Write-Host "✅ Docker containers restarted."

Write-Host "Environment cleanup complete."
