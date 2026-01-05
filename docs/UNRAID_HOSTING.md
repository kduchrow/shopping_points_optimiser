# UNRAID Docker-Hosting Anleitung für Shopping Points Optimiser

## 📋 Voraussetzungen

- UNRAID Server mit Docker Support aktiviert
- Terminal/SSH Zugang zu deinem UNRAID Server
- Mind. 2 GB RAM verfügbar
- ~5 GB Speicher für Image + Database

---

## 🚀 Schritt 1: Projekt hochladen

### Option A: Via GitHub (empfohlen)
```bash
# Auf UNRAID Terminal:
cd /mnt/user/appdata
git clone https://github.com/YOUR-USERNAME/shopping-points-optimiser.git
cd shopping-points-optimiser
```

### Option B: Manual hochladen
```bash
# SFTP/Samba Anteil:
/mnt/user/appdata/shopping-points-optimiser/
```

---

## 🔧 Schritt 2: Environment konfigurieren

```bash
cd /mnt/user/appdata/shopping-points-optimiser

# .env Datei erstellen
cp .env.example .env

# SECRET_KEY generieren
# SSH auf UNRAID und ausführen:
docker run --rm python:3.11 python -c "import secrets; print(secrets.token_hex(32))"

# Dann in .env einfügen und speichern:
# SECRET_KEY=<ausgabe-vom-kommando-oben>
nano .env
```

**Wichtige Änderungen in .env:**
- `SECRET_KEY` - Sicherer Wert (generiert)
- `ADMIN_PASSWORD` - Starkes Passwort setzen
- `DEBUG=False` - IMMER in Production!

---

## 🐳 Schritt 3: Docker Image bauen und starten

```bash
cd /mnt/user/appdata/shopping-points-optimiser

# Image bauen
docker-compose build

# Container starten
docker-compose up -d

# Status prüfen
docker-compose ps
```

### Logs anschauen
```bash
docker-compose logs -f shopping-points
```

---

## 🌐 Schritt 4: Auf UNRAID-WebGUI konfigurieren

1. **UNRAID Dashboard öffnen** → Settings → Docker
2. **Compose File hinzufügen:**
   - Copy entire content of `docker-compose.yml`
   - Oder: Compose File Path: `/mnt/user/appdata/shopping-points-optimiser/docker-compose.yml`

3. **Container konfigurieren (Optional in UNRAID UI):**
   - Name: `shopping-points-optimiser`
   - Image: auto-build aus Dockerfile
   - Port Mapping: `5000:5000` (oder anderen Port, z.B. `8080:5000`)
   - Volumes:
     - `/mnt/user/appdata/shopping-points-optimiser/instance` → `/app/instance` (Database)
     - `/mnt/user/appdata/shopping-points-optimiser` → `/app` (Code)

---

## ✅ Schritt 5: Zugang & Initialisialisierung

### Webseite öffnen
```
http://unraid-server-ip:5000/admin
```

### Datenbank initialisieren (erste Nutzung)
```bash
docker exec shopping-points-optimiser python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Datenbank erstellt!')
"
```

### Test Admin-Account erstellen
```bash
docker exec -it shopping-points-optimiser python -c "
from app import app, db
from models import User
with app.app_context():
    admin = User(username='admin', email='admin@localhost', role='Admin')
    admin.set_password('your-password')
    db.session.add(admin)
    db.session.commit()
    print('✅ Admin-Account erstellt!')
"
```

---

## 📁 Persistente Daten auf UNRAID

**Recommended AppData Structure:**
```
/mnt/user/appdata/shopping-points-optimiser/
├── instance/           ← Database (wichtig!)
├── docker-compose.yml
├── Dockerfile
├── .env                ← WICHTIG: .gitignore!
├── app.py
├── models.py
└── ...
```

**Volume Mounts in docker-compose.yml:**
```yaml
volumes:
  - /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance
  - /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs
```

---

## 🔒 Sicherheits-Checkliste

- [ ] SECRET_KEY ist zufällig generiert (min. 32 Zeichen)
- [ ] DEBUG = False in .env
- [ ] Admin-Passwort ist stark
- [ ] .env ist in .gitignore und NICHT in Git
- [ ] Database Backup regelmäßig machen
- [ ] SSL/HTTPS via Reverse Proxy (z.B. nginx in Docker)

---

## 🔄 Regelmäßige Wartung

### Container Logs prüfen
```bash
docker-compose logs shopping-points --tail 100
```

### Container updaten (Code änderungen)
```bash
cd /mnt/user/appdata/shopping-points-optimiser
git pull origin main  # wenn auf GitHub
docker-compose build --no-cache
docker-compose up -d
```

### Database Backup
```bash
cp /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db \
   /mnt/user/backups/shopping_points_backup_$(date +%Y%m%d).db
```

### Container neu starten
```bash
docker-compose restart shopping-points
```

### Container stoppen/entfernen
```bash
docker-compose down      # Stop + Remove Container
docker-compose down -v   # + Remove Volumes
```

---

## 🐛 Troubleshooting

### "Connection refused on :5000"
```bash
# Container läuft?
docker-compose ps

# Logs checken
docker-compose logs shopping-points

# Port in Verwendung?
docker ps | grep 5000
```

### "Database locked" Fehler
```bash
# Container neu starten
docker-compose restart shopping-points

# Oder alte DB backup:
rm /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db
```

### "ModuleNotFoundError"
```bash
# Requirements neu installieren
docker-compose build --no-cache
```

---

## 🌐 Reverse Proxy Setup (HTTPS)

### Via UNRAID nginx proxy
1. UNRAID: Settings → Web Terminal → nginxProxyManager Container
2. Proxy Host hinzufügen:
   - Domain: `shopping-points.yourdomain.com`
   - Forward: `shopping-points-optimiser:5000`
   - SSL: Let's Encrypt aktivieren

### Oder via separaten nginx Container
```yaml
reverse-proxy:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
  networks:
    - shopping-network
```

---

## 📊 Performance Tipps

- **Worker Prozesse**: In Dockerfile anpassen für deine Hardware
  ```dockerfile
  CMD ["gunicorn", "--workers", "8", ...]  # mehr für mehr CPU cores
  ```

- **Memory Limit** in docker-compose.yml:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 2G
  ```

- **Caching**: Redis hinzufügen für schnellere Requests
  ```yaml
  redis:
    image: redis:7-alpine
    networks:
      - shopping-network
  ```

---

## 📚 Weitere Ressourcen

- [Docker Dokumentation](https://docs.docker.com/)
- [UNRAID Docker Setup](https://docs.unraid.net/unraid-os/advanced-topics/docker/docker-containers/)
- [Flask + Gunicorn Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Shopping Points Optimiser README](../README.md)

---

## ❓ Häufige Fragen

**Kann ich PostgreSQL statt SQLite verwenden?**
Ja, aber sqlite ist für diese Größe ausreichend. Für PostgreSQL:
```yaml
# docker-compose.yml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: shopping_points
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres-data:/var/lib/postgresql/data
```
Dann: `DATABASE_URL=postgresql://user:pass@postgres:5432/shopping_points`

**Wo speichert UNRAID die Container Daten?**
Standard: `/var/lib/docker/volumes/` (intern auf Cache/Array)
AppData: `/mnt/user/appdata/` (deine Preference)

**Wie mache ich Backups?**
```bash
# Kompletter AppData Backup
tar -czf shopping_backup_$(date +%Y%m%d).tar.gz \
  /mnt/user/appdata/shopping-points-optimiser/

# Nur Database
cp instance/shopping_points.db instance/shopping_points.db.backup
```
