# Browser Extension Release Script
# Erstellt ein ZIP-Archiv für die Browser Extension

param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "🎯 Preparing Browser Extension Release v$Version..." -ForegroundColor Cyan

# Pfade
$ExtensionDir = "browser_extension"
$OutputFile = "browser_extension-v$Version.zip"

# Prüfe ob Extension-Ordner existiert
if (-not (Test-Path $ExtensionDir)) {
    Write-Host "❌ Error: $ExtensionDir not found!" -ForegroundColor Red
    exit 1
}

# Prüfe Manifest-Version
$ManifestPath = Join-Path $ExtensionDir "manifest.json"
$Manifest = Get-Content $ManifestPath | ConvertFrom-Json
$ManifestVersion = $Manifest.version

if ($ManifestVersion -ne $Version) {
    Write-Host "⚠️  Warning: manifest.json version ($ManifestVersion) differs from specified version ($Version)" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y") {
        exit 1
    }
}

# Lösche alte ZIP falls vorhanden
if (Test-Path $OutputFile) {
    Write-Host "🗑️  Removing old $OutputFile..." -ForegroundColor Yellow
    Remove-Item $OutputFile
}

# Erstelle ZIP
Write-Host "📦 Creating ZIP archive..." -ForegroundColor Green
Compress-Archive -Path "$ExtensionDir/*" -DestinationPath $OutputFile -Force

# Zeige Ergebnis
$FileSize = (Get-Item $OutputFile).Length / 1KB
Write-Host "✅ Success! Created $OutputFile ($([math]::Round($FileSize, 2)) KB)" -ForegroundColor Green

# Zeige Inhalt
Write-Host "`n📋 Archive contents:" -ForegroundColor Cyan
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $OutputFile))
$zip.Entries | ForEach-Object {
    $size = [math]::Round($_.Length / 1KB, 2)
    Write-Host "  - $($_.Name) ($size KB)"
}
$zip.Dispose()

Write-Host "`n🚀 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test the extension by loading the unpacked folder"
Write-Host "  2. Create git tag: git tag -a browser-extension-v$Version -m 'Browser Extension v$Version'"
Write-Host "  3. Push tag: git push origin browser-extension-v$Version"
Write-Host "  4. Create GitHub Release and upload $OutputFile"
Write-Host ""
