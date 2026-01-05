# Background Job Queue System

## Überblick

Das System wurde aktualisiert, um Scraper als Hintergrund-Jobs auszuführen. Dies verhindert, dass die Webseite während des Scrapings einfriert und ermöglicht es Ihnen, den Live-Fortschritt auf der Admin-Seite zu beobachten.

## Features

### 1. **Asynchrone Job-Ausführung**
- Alle Scraper (Payback, Miles & More, Example) werden jetzt im Hintergrund ausgeführt
- Die Admin-Seite antwortet sofort mit einer Job-ID
- Der Scraper läuft parallel weiter

### 2. **Live-Progress-Tracking**
- Progress-Bar mit Live-Update (aktualisiert alle 500ms)
- Job-Status: `QUEUED` → `RUNNING` → `COMPLETED` oder `FAILED`
- Detaillierte Echtzeit-Meldungen aus dem Scraper

### 3. **Job-Lifecycle**
- **Job-Queue**: `job_queue.py` verwaltet eine Thread-basierte Queue
- **Worker-Thread**: Ein Daemon-Thread verarbeitet Jobs nacheinander
- **Completion**: Nach erfolgreicher Beendigung wird die Seite automatisch neugeladen

## Architektur

### `job_queue.py` - Job Queue Manager
```python
class JobQueue:
    - enqueue(func, args, kwargs) -> job_id  # Job in Queue einfügen
    - get_job(job_id) -> Job  # Job-Status abrufen
    - get_all_jobs() -> List[Job]  # Alle Jobs abrufen
    - start()  # Worker-Thread starten
    - stop()  # Worker-Thread beenden
```

### `Job` - Einzelner Job
```python
class Job:
    - status: JobStatus (QUEUED, RUNNING, COMPLETED, FAILED)
    - progress: int (0-100%)
    - messages: List[str]  # Detaillierte Meldungen
    - result: Any  # Rückgabewert
    - error: Optional[str]  # Fehler, falls vorhanden
    - to_dict() -> dict  # JSON-Serialisierung
```

## Verwendung

### Admin-Panel
1. Rufen Sie `/admin` auf
2. Klicken Sie auf einen Scraper-Button (z.B. "Run Payback Scraper")
3. Die Job-Progress-Box wird angezeigt
4. Live-Updates der Progress-Bar und Meldungen sehen Sie in Echtzeit
5. Nach Abschluss wird die Seite automatisch neugeladen

### API-Endpoints

#### Job-Status abrufen
```bash
GET /admin/job_status/<job_id>
```
Antwort:
```json
{
  "id": "a1b2c3d4-...",
  "status": "running",
  "progress": 50,
  "progress_percent": 50,
  "total_steps": 100,
  "messages": [
    {"timestamp": "2026-01-05T10:30:45.123456", "message": "Fetche Daten..."},
    {"timestamp": "2026-01-05T10:30:50.654321", "message": "Registriere Daten..."}
  ],
  "error": null,
  "result": null,
  "created_at": "2026-01-05T10:30:40.000000",
  "started_at": "2026-01-05T10:30:42.000000",
  "completed_at": null
}
```

#### Alle Jobs abrufen
```bash
GET /admin/jobs
```
Antwort: Array der letzten 20 Jobs mit obiger Struktur

### Routes für Scraper
```
POST /admin/run_scraper      → Example Scraper
POST /admin/run_payback      → Payback Scraper
POST /admin/run_miles_and_more → Miles & More Scraper
```

Antwort (JSON):
```json
{
  "job_id": "a1b2c3d4-...",
  "status": "queued"
}
```

## Integration in Scraper-Funktionen

Jede Scraper-Funktion erhält ein `Job`-Objekt als ersten Parameter:

```python
def scrape_payback(job):
    """Background job for Payback scraper"""
    with app.app_context():
        job.add_message('Starte Payback-Scraper...')
        job.set_progress(10, 100)
        
        # ... scraping logic ...
        
        job.add_message('Daten verarbeitet')
        job.set_progress(80, 100)
        
        # ... more logic ...
        
        job.set_progress(100, 100)
        return {'added': added, 'updated': updated}
```

### Job-Methoden im Scraper
- `job.add_message(msg)` - Status-Meldung hinzufügen
- `job.set_progress(current, total)` - Progress aktualisieren
- `job.get_progress_percent()` - Progress in % abrufen

## Frontend - Admin-Template

Das Admin-Template (`templates/admin.html`) zeigt:
1. **Job-Progress-Box** mit Live-Updates
   - Status-Badge (QUEUED/RUNNING/COMPLETED/FAILED)
   - Progress-Bar mit Prozentsatz
   - Detaillierte Meldungen (scrollable)

2. **Scraper-Buttons** mit Event-Listener
   - Senden AJAX-Request mit `Accept: application/json`
   - Empfangen Job-ID zurück
   - Starten Live-Polling automatisch

3. **Auto-Reload** nach Abschluss
   - Nach 2 Sekunden wird die Seite neugeladen
   - Zeigt aktualisierte Shop-Daten und neue Logs

## Technische Details

### Thread-Sicherheit
- `JobQueue` nutzt `threading.Lock()` für Thread-Safe Access
- Jeder Job läuft in eigenem Daemon-Thread
- App-Context wird für DB-Zugriffe korrekt gesetzt

### Worker-Thread
- Läuft im Hintergrund (`daemon=True`)
- Verarbeitet Jobs aus Queue sequenziell
- Schläft 100ms, wenn Queue leer ist (verhindert busy-waiting)

### Speicher-Management
- `job_queue.clear_old_jobs(max_age_hours=24)` kann aufgerufen werden
- Entfernt abgeschlossene/fehlgeschlagene Jobs älter als 24 Stunden
- Kann in Cron-Job oder Maintenance-Route aufgerufen werden

## Fehlerbehandlung

Wenn ein Job fehlschlägt:
1. Exception wird abgefangen
2. `job.error` wird gesetzt
3. `job.status` wird auf `FAILED` gesetzt
4. Error-Meldung wird zu `job.messages` hinzugefügt
5. Frontend zeigt roten FAILED-Status
6. Auto-Reload erfolgt NICHT (zum Debuggen)

## Performance

- **Payback Scraper**: Ca. 30-60 Sekunden (mehrere hundert Partners)
- **Miles & More Scraper**: Ca. 60-120 Sekunden (komplexer)
- **Example Scraper**: Ca. 5-10 Sekunden

Die Website bleibt vollständig responsiv während des Scrapings!

## Debugging

### Logs anschauen
```bash
# Admin-Seite zeigt alle Logs
http://127.0.0.1:5000/admin
```

### Job-Status im Browser prüfen
```javascript
// In Browser-Konsole:
fetch('/admin/job_status/<job_id>').then(r => r.json()).then(console.log)
```

### Job-Queue im Code debuggen
```python
from job_queue import job_queue

# Alle Jobs
all_jobs = job_queue.get_all_jobs()
for job in all_jobs:
    print(f"{job.id}: {job.status.value} - {job.progress}%")
    print(f"  Messages: {job.messages}")
```

## Zukünftige Verbesserungen

- [ ] Persistent Job Storage (DB statt Memory)
- [ ] Job-History und Statistiken
- [ ] Parallelisierung mehrerer Jobs (aktuell sequential)
- [ ] Webhooks bei Job-Completion
- [ ] Job-Retry bei Fehler
- [ ] Scheduled Jobs (z.B. tägliche Scraper)
