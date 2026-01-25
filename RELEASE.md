# Release Process

## Browser Extension Release

### 1. Version aktualisieren

- Passe `browser_extension/manifest.json` an (z.B. `1.0.1`).

### 2. GitHub Actions Workflow (empfohlen)

Workflow: `.github/workflows/extension-release.yml`

- Trigger per Tag: `browser-extension-v*`
- Optional: Manuell via `workflow_dispatch`
- Output: ZIP **und** CRX werden gebaut.

**Schlüssel-Handling (CRX):**

- Format: Unverschlüsselter RSA/PKCS#8-Privatkey im PEM-Format (`-----BEGIN PRIVATE KEY-----`). Encrypted, OpenSSH, oder P12/PFX Keys funktionieren nicht.
- Variante A (empfohlen): Lege den privaten Schlüssel-Inhalt direkt als Secret `EXTENSION_PEM` (roh als Text). Der Workflow legt daraus temporär `key.pem` an.
- Variante B: Falls nötig, als Base64 kodiert in `EXTENSION_PEM_B64`. Erzeuge die Base64 ohne Zeilenumbrüche, z. B. `base64 -w 0 key.pem` (Linux) oder `base64 key.pem | tr -d '\n'` (macOS). Der Workflow dekodiert mit `--ignore-garbage`.
- Konvertieren zu unverschlüsselt (falls dein Key verschlüsselt oder OpenSSH ist):

```bash
openssl pkcs8 -topk8 -nocrypt -in key.pem -out key_unencrypted.pem
```

- `.pem` bleibt in `.gitignore` und wird nie ins Repo committet.

**Ablauf Tag-basiert:**

```bash
# Commit & Push
git add .
git commit -m "chore: prepare browser extension v1.0.1"
git push origin feature/browser_extension

# Tag setzen
git tag -a browser-extension-v1.0.1 -m "Browser Extension v1.0.1"
git push origin browser-extension-v1.0.1
# → Workflow baut browser_extension-1.0.1.zip und .crx und hängt sie an das Release
```

**Manuell (workflow_dispatch):**

1. Actions → "Browser Extension Release" → Run workflow (Branch oder Tag wählen)
2. Artefakte: `browser_extension-<version>.zip` und `.crx`
3. Bei Tag-Push werden sie als Release-Assets veröffentlicht

### 3. Release-Beschreibung (Template)

```markdown
## 🎯 Shopping Points Optimiser - Browser Extension v1.0.1

### ✨ Features

- Automatische Shop-Erkennung auf allen Webseiten
- Gruppierte Bonusprogramme nach effektivem Wert
- Performance-optimierte Shop-Suche
- URL-Proposals direkt aus der Extension

### 📦 Installation

1. Lade `browser_extension-1.0.1.crx` oder `.zip` herunter
2. `chrome://extensions/` öffnen, Entwicklermodus aktivieren
3. Drag & Drop der `.crx` oder "Entpackte Erweiterung laden" für die entpackte ZIP

### 🔧 Changelog

- feat: Gruppierte Bonusprogramme mit Best-Value-Sortierung
- perf: Search-on-type statt vollständiger Shop-Liste
- feat: Zentrale API_BASE_URL Konfiguration
- fix: Shop-Auswahl Synchronisation
```

## App Release (Docker)

- Tags: `v{MAJOR}.{MINOR}.{PATCH}`
- Build/Push: siehe `.github/workflows/deploy.yml`

## Versioning

- Browser Extension: `browser-extension-v{MAJOR}.{MINOR}.{PATCH}`
- App: `v{MAJOR}.{MINOR}.{PATCH}`
