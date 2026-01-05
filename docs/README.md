# Shopping Points Optimiser

Community-getriebenes Flask-Projekt zum Vergleich verschiedener Bonusprogramme und Shops.

## Features

- 💳 **Einkaufs-Szenario**: Vergleich von Points/Cashback bei Einkäufen
- 🎁 **Gutschein-Optimierung**: Berechnung benötigter Umsätze für Gutscheine
- ✍️ **Vertragsabschlüsse**: Einmalige Bonuspunkte bei Vertragsabschluss
- 👥 **Community-System**: Rollenbasiertes User-Management mit Proposals & Voting
- 🤖 **Scraper**: Automatisches Laden von Bonus-Raten (z.B. Payback)

## Setup (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python app.py
```

Öffne dann http://127.0.0.1:5000

Die Datenbank `shopping.db` wird beim ersten Start angelegt und mit Beispiel-Daten gefüllt.

## Test-Accounts

Für Entwicklung und Testing stehen folgende Accounts zur Verfügung:

| Rolle        | Benutzername  | Passwort     | Berechtigungen                                    |
|--------------|---------------|--------------|---------------------------------------------------|
| Admin        | `admin`       | `admin123`   | Voller Zugriff, Admin-Seite, User-Management     |
| Contributor  | `contributor` | `contrib123` | Proposals erstellen & abstimmen                   |
| User         | `testuser`    | `user123`    | Proposals erstellen, nur ansehen (kein Voting)    |
| Viewer       | `viewer`      | `viewer123`  | Tool nutzen ohne Registrierung                    |

**Hinweis:** Diese Accounts werden automatisch beim ersten Start erstellt. In Produktion sollten sichere Passwörter verwendet werden.

Test-Accounts manuell erstellen:
```powershell
python create_test_accounts.py
```

## Struktur

```
shopping_points_optimiser/
├── bonus_programs/     # Plugins für Bonusprogramme (MilesAndMore, Payback, Shoop)
├── shops/              # Plugins für Shops und deren Raten
├── scrapers/           # Web-Scraper für automatisches Daten-Laden
│   ├── base.py         # BaseScraper-Klasse
│   └── payback_scraper_js.py  # Payback-Scraper mit Playwright
├── templates/          # HTML-Templates (Jinja2)
│   ├── index.html      # Startseite mit Berechnungsformular
│   ├── result.html     # Ergebnisseite
│   ├── admin.html      # Admin-Dashboard
│   ├── login.html      # Login-Seite
│   ├── register.html   # Registrierungs-Seite
│   ├── profile.html    # User-Profil
│   └── proposals.html  # Community-Proposals
├── models.py           # SQLAlchemy-Modelle (User, Shop, Proposal, etc.)
├── app.py              # Flask-App mit allen Routes
└── requirements.txt    # Python-Dependencies
```

## User-Rollen

### Viewer (Standard bei Registrierung)
- Kann Tool nutzen (Berechnungen)
- Kann keine Proposals erstellen oder abstimmen

### User
- Kann Proposals erstellen
- Kann Proposals ansehen
- Kann **nicht** abstimmen

### Contributor
- Kann Proposals erstellen
- Kann über Proposals abstimmen (Upvote/Downvote)
- **3+ Upvotes** = automatische Approval
- Muss von Admin promoted werden

### Admin
- Voller Zugriff auf alle Funktionen
- User-Management (promote, ban)
- Scraper-Ausführung
- Shops & Programme manuell hinzufügen

## Scraper

### Payback-Scraper

In der Admin-Seite (`/admin`) auf "▶ Run Payback Scraper" klicken.

Der Payback-Scraper:
- Nutzt Playwright für JavaScript-Rendering
- Klickt "Mehr anzeigen"-Button automatisch
- Extrahiert Points/EUR und Cashback-Werte
- Findet ~720 Partner-Shops
- Historisiert Rate-Änderungen automatisch

## Community-Proposals

### Proposal-Types

1. **rate_change**: Änderung von Points/EUR oder Cashback%
2. **shop_add**: Neuen Shop hinzufügen
3. **program_add**: Neues Bonusprogramm hinzufügen
4. **coupon_add**: Sonderaktion/Coupon hinzufügen

### Sonderaktionen (Coupons)

Sonderaktionen sind zeitlich begrenzte Bonuspunkte-Multiplikatoren oder Rabatte, die von der Community eingereicht und verwaltet werden.

**Coupon-Typen:**
- **Multiplier**: z.B. "20x Punkte bei Payback" (5.000€ Einkauf = 20.000 Punkte)
- **Discount**: z.B. "10% Rabatt auf Partner-Einkauf"

**Eigenschaften:**
- Können universal, shop-spezifisch oder programm-spezifisch sein
- Kombinierbarkeit kann definiert sein (ja/nein) oder unbekannt
- Mit Gültigkeitsdatum (valid_from / valid_to)
- Werden bei der Berechnung automatisch berücksichtigt

**Berechnung mit Coupons:**
- Wenn aktive Coupons vorhanden: Beide Werte werden angezeigt
- Basiswert + Mit Sonderaktion
- ⚠️ Warnung wenn Kombinierbarkeit unbekannt ist

**Beispiel Proposal:**
```
Art: Coupon-Add
Aktion: Multiplikator 20x
Beschreibung: "20-fach Punkte bei Zahlungszielen ab 50€"
Shop: Payback (optional)
Gültig bis: 31.12.2024
Kombinierbar: Unbekannt
```

### Approval-Workflow

1. User/Contributor erstellt Proposal
2. Contributors stimmen ab (Upvote/Downvote)
3. Bei **3+ Upvotes**: Automatische Approval
4. Status wechselt zu "approved"
5. Änderung wird in DB übernommen

## Admin-Funktionen

### Zugriff
Nur User mit `role='admin'` können auf `/admin` zugreifen.

### Features
- Scraper ausführen
- Shops nach Name/Programm filtern (Top 20)
- Neue Bonusprogramme hinzufügen
- Contributor-Requests genehmigen
- User-Status ändern (ban/unban)
- Scraper-Logs einsehen (neueste 50)

## Technologie-Stack

- **Backend**: Flask + SQLAlchemy
- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Auth**: Flask-Login
- **Scraping**: Playwright (Chromium)
- **Database**: SQLite
- **Password-Hashing**: werkzeug.security

## Entwicklung

### Database Migrations

Bei Schema-Änderungen:
```powershell
# Aktuelle DB löschen (Vorsicht: alle Daten gehen verloren!)
del shopping.db
python app.py  # Neu erstellen mit neuem Schema
```

### Debugging

```python
# In app.py
app.run(debug=True)  # Auto-Reload bei Code-Änderungen
```

## Rechtliche Hinweise

- Scraper sollten `robots.txt` respektieren
- Nutzungsbedingungen der Websites beachten
- Rate-Limiting implementieren
- Nur für private, nicht-kommerzielle Nutzung
