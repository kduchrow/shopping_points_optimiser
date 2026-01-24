# Shopping Points Optimiser - Browser Extension

Eine Chrome/Chromium Extension für den Shopping Points Optimiser.

## Features

✅ **Automatische Shop-Erkennung**: Erkennt automatisch, wenn du auf einer Shop-Seite bist
✅ **Badge-Benachrichtigung**: Zeigt ein Ausrufezeichen (!) am Extension-Icon, wenn ein Shop erkannt wurde
✅ **Beste Rates anzeigen**: Beim Klick auf das Icon werden die besten Bonusprogramme für den Shop angezeigt
✅ **URL-Proposal erstellen**: Wenn ein Shop nicht erkannt wurde, kannst du direkt einen Vorschlag erstellen (Login erforderlich)
✅ **Sofortige Anzeige**: Nach dem Erstellen eines Proposals werden die Rates direkt angezeigt

## Installation (Entwicklungsmodus)

1. **Chrome/Chromium öffnen**
2. **Extensions-Seite öffnen**:
   - Gehe zu `chrome://extensions/`
   - Oder: Menü → Weitere Tools → Erweiterungen
3. **Entwicklermodus aktivieren**:
   - Schalte den Entwicklermodus oben rechts ein
4. **Extension laden**:
   - Klicke auf "Entpackte Erweiterung laden"
   - Wähle den Ordner `browser_extension` aus diesem Repository

## Verwendung

### Shop erkannt

1. Besuche eine Shop-Webseite (z.B. Amazon, Zalando, etc.)
2. Wenn der Shop erkannt wurde, erscheint ein **Ausrufezeichen (!)** am Extension-Icon
3. Klicke auf das Icon, um die besten Bonusprogramme zu sehen:
   - 🏆 Beste Rate wird hervorgehoben
   - 📊 Alle verfügbaren Bonusprogramme werden aufgelistet
   - Details: Punkte/€, Cashback %, Incentive-Texte

### Shop nicht erkannt

1. Wenn kein Shop erkannt wurde, siehst du eine "Shop nicht erkannt"-Meldung
2. **Mit Login**: Du kannst direkt einen Vorschlag erstellen:
   - Wähle den passenden Shop aus der Liste
   - Bestätige die URL
   - Klicke auf "Vorschlag erstellen"
   - Die Rates werden dir sofort angezeigt!
3. **Ohne Login**: Du wirst aufgefordert, dich anzumelden

## API-Endpoints

Die Extension benötigt folgende API-Endpoints:

- `GET /api/shops` - Liste aller Shops
- `GET /api/shops/{id}/rates` - Rates für einen Shop
- `GET /api/user/status` - Login-Status prüfen
- `POST /api/proposals/url` - URL-Proposal erstellen

## Konfiguration

### API Base URL ändern

In `background.js` und `popup.js`:

```javascript
const API_BASE_URL = "http://localhost:5000"; // Für Development
// const API_BASE_URL = 'https://your-domain.com'; // Für Production
```

### Host Permissions

In `manifest.json` kannst du die Host Permissions anpassen:

```json
"host_permissions": [
  "http://localhost:5000/*",
  "https://your-domain.com/*"
]
```

## Technische Details

### Manifest V3

Die Extension verwendet Manifest V3 (neueste Version):

- **Service Worker** statt Background Pages
- **chrome.action** API für das Popup
- **chrome.storage.local** für Tab-spezifische Daten

### Architektur

```
browser_extension/
├── manifest.json          # Extension-Konfiguration
├── background.js          # Service Worker (Shop-Erkennung, Badge-Updates)
├── content.js             # Content Script (läuft auf jeder Seite)
├── popup.html             # Popup UI
├── popup.js               # Popup Logik
├── popup.css              # Popup Styling
├── icons/                 # Extension Icons
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md             # Diese Datei
```

### Shop-Matching

Die Extension matched Shops anhand der URL:

- Vergleicht Hostname der aktuellen Seite mit Shop-URLs
- Prüft auch alternative URLs
- Cache-Mechanismus (5 Minuten) zur Performance-Optimierung

## Development

### Debugging

- **Background Script**: `chrome://extensions/` → "Service Worker" Link
- **Popup**: Rechtsklick auf Popup → "Untersuchen"
- **Content Script**: Browser DevTools auf der Webseite

### Logs

Die Extension loggt wichtige Events in die Console:

- Shop-Matches
- API-Requests
- Fehler

## TODO / Geplante Features

- [ ] Icons erstellen (aktuell Platzhalter)
- [ ] Firefox-Kompatibilität
- [ ] Offline-Modus mit lokalem Cache
- [ ] Benachrichtigungen bei neuen Rates
- [ ] Historische Rate-Vergleiche
- [ ] Quick-Actions (direkt zum Partner-Portal)

## Support

Bei Fragen oder Problemen erstelle bitte ein Issue im Repository.

## Lizenz

Siehe LICENSE im Root-Verzeichnis des Repositories.
