# Migration: Raten‑Sichtbarkeit & User‑spezifische Raten

**Hinweis:** Dieses Dokument ist **keine Rechtsberatung**. Bitte juristisch prüfen lassen, ob die Maßnahmen für euren konkreten Fall ausreichend sind.

Ziel: Öffentliche Darstellung von Raten vermeiden; stattdessen nur die Information „Shop ↔ Bonusprogramm vorhanden“ anzeigen. Individuelle Raten werden ausschließlich vom Nutzer selbst gepflegt.

---

## Leitprinzip (rechtlich konservativer Weg)

1. **Keine öffentliche Veröffentlichung von Konditionen/Raten**.
2. **Nur Relation anzeigen** (Shop ↔ Bonusprogramm vorhanden).
3. **User‑spezifische Raten** ausschließlich auf Basis eigener Eingaben.
4. **Scraper/Importe** dürfen für „private“ Programme **keine Raten** persistent speichern.

---

## Phase 1 — Programmsichtbarkeit (Option B / MVP)

### 1.1 Datenmodell

**BonusProgram** erhält ein Sichtbarkeitsfeld:
- `visibility`: Enum/String
  - `public` → Raten öffentlich anzeigen
  - `relation_only` → nur Beziehung anzeigen
  - `private` → nur user‑spezifische Raten

### 1.2 Migration

- Alembic Migration: `Add visibility to BonusProgram`.
- Default: `public`.

### 1.3 Admin UI

- Programmliste erweitert um Sichtbarkeits‑Dropdown.
- Änderungen nur durch Admin.

### 1.4 Öffentliche Views

- Bei `visibility != public`:
  - Keine Raten anzeigen.
  - Stattdessen Text: „Beziehung vorhanden – Raten sind nutzerspezifisch“.

### 1.5 Ingest / Scraper

- Wenn `visibility != public`:
  - **Raten nicht speichern**.
  - Optional: nur Shop‑Relation erhalten (falls benötigt).

### 1.6 Datenbereinigung (für private Programme)

- Bestehende Raten löschen oder deaktivieren:
  - `ShopProgramRate.valid_to = now` für betroffene Programme.

---

## Phase 2 — User‑spezifische Raten (Option C / sauber)

### 2.1 Datenmodell

Neue Tabelle **UserProgramRate**:
- `id`
- `user_id` (FK)
- `shop_id` (FK)
- `program_id` (FK)
- `points_per_eur`, `cashback_pct`, `points_absolute`, `cashback_absolute`
- `valid_from`, `valid_to`
- `notes`

Unique Constraint:
- `(user_id, shop_id, program_id)`

### 2.2 Migration

- Alembic Migration: `Create user_program_rate`.

### 2.3 API

- `GET /api/user-rates`
- `POST /api/user-rates`
- `DELETE /api/user-rates/<id>`

Nur für eingeloggte Nutzer.

### 2.4 UI

- Ergebnisansicht:
  - Wenn Programm `private`/`relation_only`: Eingabeformular „Meine Rate hinzufügen“.
- Profilseite:
  - Liste/CRUD für eigene Raten.

### 2.5 Berechnung

- Wenn Programm `visibility != public`:
  - Nur `UserProgramRate` nutzen.
- Sonst `ShopProgramRate` wie bisher.

---

## Rechtlich konservative Betriebsregeln

1. **Private Programme als `private` markieren**.
2. **Keine Speicherung von Scraper‑Raten** für `private` Programme.
3. **Nur Nutzer‑eingetragene Raten** für private Programme verwenden.
4. **Keine Ausgabe von Raten in öffentlichen Views**.

---

## Rollout‑Checkliste

### Phase 1 (MVP)
- [ ] Migration `visibility` ausrollen
- [ ] Admin‑UI aktualisieren
- [ ] Öffentliche Views filtern
- [ ] Scraper‑Ingest blockieren für `private`
- [ ] Bestandsraten für private Programme deaktivieren

### Phase 2 (User‑Rates)
- [ ] Neue Tabelle + Migration
- [ ] API CRUD
- [ ] UI Eingabe/Verwaltung
- [ ] Evaluation anpassen

---

## Risiko‑Hinweis

- Das Dokument ersetzt keine Rechtsberatung.
- Veröffentlichung von Raten/Konditionen kann trotz technischer Maßnahmen rechtlich problematisch sein.
- Bitte vor Live‑Gang rechtliche Prüfung durchführen.
