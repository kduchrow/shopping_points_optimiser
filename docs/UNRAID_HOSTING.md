# UNRAID Docker-Hosting Anleitung für Shopping Points Optimiser

## 📋 Voraussetzungen

- UNRAID Server mit Docker Support aktiviert
- SSH/Terminal Zugang zu deinem UNRAID Server (nur für Setup)
- Mind. 2 GB RAM verfügbar
- ~5 GB Speicher für Image + Database
- GitHub Account (optional, aber empfohlen)

---

## 🚀 Setup für UNRAID WebGUI

### Schritt 1: Projekt auf UNRAID hochladen

**Option A: Via GitHub (empfohlen)**
```bash
# SSH in dein UNRAID System
ssh root@unraid-ip

# Zum appdata Verzeichnis gehen
cd /mnt/user/appdata

# Von GitHub klonen
git clone https://github.com/YOUR-USERNAME/shopping-points-optimiser.git
cd shopping-points-optimiser
```

**Option B: Manuell via SFTP**
1. WinSCP oder FileZilla öffnen
2. Verbinden zu UNRAID Server
3. Navigiere zu `/mnt/user/appdata/shopping-points-optimiser/`
4. Kopiere alle Projekt-Dateien dort hin

---

### Schritt 2: Environment Datei erstellen (SSH)

```bash
# SSH Terminal:
cd /mnt/user/appdata/shopping-points-optimiser

# .env Datei von Template erstellen
cp .env.example .env

# SECRET_KEY generieren
docker run --rm python:3.11 python -c "import secrets; print(secrets.token_hex(32))"

# Output kopieren! Z.B.: a1b2c3d4e5f6abc123...

# .env Datei editieren
nano .env
```

**Wichtige Änderungen in .env:**
```env
SECRET_KEY=a1b2c3d4e5f6abc123...  # ← Paste die generierte KEY hier!
ADMIN_PASSWORD=DeinStarkesPasswort  # ← Ändern!
DEBUG=False  # ← IMMER False in Production!
```

Speichern: `CTRL+X` → `Y` → `ENTER`

---

### Schritt 3: Docker Image bauen (SSH - einmalig!)

**WICHTIG:** UNRAID WebGUI kann keine Images bauen, nur starten!

```bash
# SSH Terminal:
cd /mnt/user/appdata/shopping-points-optimiser

# WICHTIG: Erstelle Verzeichnisse für Volumes
mkdir -p instance logs
chmod -R 777 instance logs

# Image bauen (dauert 2-5 Minuten beim ersten Mal)
docker build -t shopping-points-optimiser:latest .

# Prüfen ob Image gebaut wurde
docker images | grep shopping-points
# Sollte zeigen: shopping-points-optimiser   latest   ...

# WICHTIG: Testen ob gunicorn im Image ist!
docker run --rm shopping-points-optimiser:latest which gunicorn
# Sollte zeigen: /root/.local/bin/gunicorn

# Wenn "gunicorn not found" → Image nochmal neu bauen!
docker build --no-cache -t shopping-points-optimiser:latest .
```

**Troubleshooting beim Build:**
```bash
# Falls Build fehlschlägt:
# 1. Prüfe ob requirements.txt gunicorn enthält
grep gunicorn requirements.txt
# Sollte zeigen: gunicorn>=...

# 2. Build mit mehr Output
docker build --no-cache --progress=plain -t shopping-points-optimiser:latest .

# 3. Prüfe Docker Logs
docker logs $(docker ps -aq --filter name=shopping-points) 2>&1 | tail -50
```

---

### Schritt 4: Container in UNRAID WebGUI hinzufügen

Jetzt kannst du die UNRAID WebGUI nutzen!

1. **UNRAID Dashboard öffnen** → **Docker** Tab
2. Click auf **Add Container**
3. Folgende Einstellungen eingeben:

**Basic Settings:**
```
Name: shopping-points-optimiser
Repository: shopping-points-optimiser:latest
```
⚠️ **WICHTIG:** Kein "dockerhub.io/" oder ähnliches - nur `shopping-points-optimiser:latest`!

**Advanced Settings:**
```
Network Type: bridge
Console shell command: Bash
```

---

### Schritt 5: Port Mapping konfigurieren

Click auf **Add another Path, Port, Variable, Label or Device**

**Port 1:**
```
Config Type: Port
Name: WebUI
Container Port: 5000
Host Port: 5000
Connection Type: TCP
```

---

### Schritt 6: Volume Mappings konfigurieren

**Volume 1 (Database):**
```
Config Type: Path
Name: Database
Container Path: /app/instance
Host Path: /mnt/user/appdata/shopping-points-optimiser/instance
Access Mode: Read/Write
```

**Volume 2 (Logs):**
```
Config Type: Path
Name: Logs
Container Path: /app/logs
Host Path: /mnt/user/appdata/shopping-points-optimiser/logs
Access Mode: Read/Write
```

⚠️ **WICHTIG:** Mounte NICHT das komplette `/app` Verzeichnis! 
Das überschreibt die installierten Python-Packages im Container!

Nur `instance` und `logs` mounten!

---

### Schritt 7: Environment Variables setzen

**Variable 1:**
```
Config Type: Variable
Name: SECRET_KEY
Key: SECRET_KEY
Value: <dein-generierter-secret-key>
```

**Variable 2:**
```
Config Type: Variable
Name: ADMIN_PASSWORD
Key: ADMIN_PASSWORD
Value: DeinStarkesPasswort
```

**Variable 3:**
```
Config Type: Variable
Name: DEBUG
Key: DEBUG
Value: False
```

**Variable 4:**
```
Config Type: Variable
Name: FLASK_ENV
Key: FLASK_ENV
Value: production
```

---

### Schritt 8: Container starten!

1. Scroll nach unten
2. Click auf **Apply**
3. UNRAID wird den Container starten

**Container sollte jetzt "Started" Status haben!**

**Das war's! 🎉** 

Die App initialisiert automatisch beim ersten Start:
- ✅ Datenbank-Tabellen werden erstellt
- ✅ Bonus-Programme werden registriert (Miles & More, Payback, Shoop)
- ✅ Admin-Account wird angelegt (mit ADMIN_PASSWORD aus .env)

Prüfe die Logs um zu sehen dass alles geklappt hat:
```bash
docker logs shopping-points-optimiser --tail 50
# Sollte zeigen: "✅ Admin user created successfully"
```

---

## ✅ Zugang testen

### Webseite öffnen
```
http://unraid-server-ip:5000/admin
```

**Login:**
- Username: `admin`
- Password: Das Passwort aus deiner .env Datei (ADMIN_PASSWORD)

🎉 **Fertig! Dein Shopping Points Optimiser läuft jetzt auf UNRAID!**

---

## 📁 Persistente Daten auf UNRAID

**AppData Struktur:**
```
/mnt/user/appdata/shopping-points-optimiser/
├── instance/
│   └── shopping_points.db    ← Deine Daten!
├── Dockerfile
├── docker-compose.yml
├── .env                      ← NICHT in Git!
├── app.py
└── ...
```

**Wichtig:** Diese Dateien werden automatisch persistent gespeichert, auch wenn der Container neu startet!

---

## 🔒 Sicherheits-Checkliste

- [ ] SECRET_KEY ist zufällig generiert (min. 32 Zeichen)
- [ ] DEBUG = False in .env
- [ ] Admin-Passwort ist stark (min. 12 Zeichen)
- [ ] `.env` ist in `.gitignore` und NICHT in Git
- [ ] Database Backups regelmäßig machen
- [ ] Port 5000 nur im LAN zugänglich (oder via Reverse Proxy mit SSL)



---

## 🔄 Regelmäßige Wartung auf UNRAID

### Container Status prüfen
```bash
cd /mnt/user/appdata/shopping-points-optimiser

# Status anschauen
docker ps | grep shopping-points

# Logs prüfen (letzte 50 Zeilen)
docker logs shopping-points-optimiser --tail 50

# Live Logs verfolgen
docker logs -f shopping-points-optimiser
```

### Code updaten (wenn von GitHub)
```bash
cd /mnt/user/appdata/shopping-points-optimiser

# Container stoppen und entfernen
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser

# WICHTIG: Altes Image entfernen, damit das neue verwendet wird!
docker rmi shopping-points-optimiser:latest

# Neueste Version holen
git pull origin main

# Image neu bauen
docker build -t shopping-points-optimiser:latest .

# Prüfen dass neues Image gebaut wurde
docker images | grep shopping-points-optimiser
# Image ID sollte neu sein!
```

**Dann in UNRAID WebGUI:**
1. Gehe zum Docker Tab
2. Finde deinen Container "shopping-points-optimiser"
3. Click auf das Container Icon → **Edit**
4. Click einfach auf **Apply** (ohne etwas zu ändern)
5. UNRAID startet den Container neu mit dem neuesten Image

**Alternative via SSH:**
```bash
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

### Database Backup
```bash
# Backup erstellen
cp /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db \
   /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points_$(date +%Y%m%d).db.backup

echo "✅ Backup erstellt!"
```

### Container neu starten
```bash
# Soft restart (nur Container neu starten, gleiches Image)
docker restart shopping-points-optimiser

# Hard restart (mit neu gebautem Image)
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser

# Altes Image entfernen (wichtig!)
docker rmi shopping-points-optimiser:latest

# Image neu bauen
docker build -t shopping-points-optimiser:latest .

# In UNRAID WebGUI: Docker Tab → Edit Container → Apply
# Oder via SSH:
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

**💡 Tipp:** UNRAID WebGUI erkennt automatisch neue Images wenn du "Edit" → "Apply" drückst!

---

## 🐛 Troubleshooting für UNRAID

### Container startet nicht
```bash
# Logs anschauen für Fehler
docker logs shopping-points-optimiser

# Docker Image mal neu bauen
docker stop shopping-points-optimiser 2>/dev/null
docker rm shopping-points-optimiser 2>/dev/null
docker build --no-cache -t shopping-points-optimiser:latest .
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 5000:5000 \
  --network shopping-network \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

### "Connection refused" auf Port 5000
```bash
# Läuft der Container?
docker ps | grep shopping-points
# Status sollte "Up X minutes" sein

# Läuft er auf Port 5000?
docker port shopping-points-optimiser

# Firewall blockt Port?
# UNRAID Dashboard → Ipv4/IPv6 Port Check: 5000 öffnen

# Oder anderen Port nutzen:
# Container neu mit anderem Port starten:
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 8080:5000 \
  --network shopping-network \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
# Dann: http://unraid-ip:8080/admin
```

### Database Fehler / Korruption
```bash
# Container stoppen
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser

# Alte DB löschen/backupen
mv /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db \
   /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db.old

# Container neu starten (erstellt frische DB automatisch)
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

### "unable to open database file" Fehler
```bash
# Problem 1: Falsche Datei existiert (shopping.db statt shopping_points.db)
cd /mnt/user/appdata/shopping-points-optimiser/instance
ls -la
# Falls shopping.db (ohne _points) existiert:
rm -f shopping.db

# Problem 2: Verzeichnis-Permissions
cd /mnt/user/appdata/shopping-points-optimiser
chmod -R 777 instance logs

# Container neu starten
docker restart shopping-points-optimiser

# Logs prüfen
docker logs shopping-points-optimiser --tail 50
# Sollte zeigen: "✅ Database tables initialized"
```

### "ModuleNotFoundError" oder ImportError
```bash
# Container stoppen und neu bauen
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser
docker build --no-cache -t shopping-points-optimiser:latest .
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 5000:5000 \
  --network shopping-network \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

### Speicher voll
```bash
# Logs prüfen
du -sh /mnt/user/appdata/shopping-points-optimiser/

# Docker Cleanup
docker system prune -a  # Vorsicht: Löscht alle ungenutzten Images!

# Oder nur Dangling:
docker image prune
```

---

## 🌐 HTTPS / Reverse Proxy für UNRAID

Falls du HTTPS brauchst:

### Option 1: Nginx Proxy Manager (einfach)
```bash
# Neuen Container hinzufügen:
# Image: jlesage/nginx-proxy-manager
# Ports: 80:8080, 443:8443, 81:81
# 
# Dann in WebUI (Port 81):
# Proxy Hosts → New
# Domain: shopping.yourdomain.com
# Scheme: http
# Forward Hostname: shopping-points-optimiser
# Forward Port: 5000
# SSL: Let's Encrypt
```

### Option 2: Caddy Reverse Proxy
```yaml
# Zusätzlich in docker-compose.yml:
  caddy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    networks:
      - shopping-network
```

---

## 📊 Performance Tipps für UNRAID

**Wenn Container langsam ist:**

1. **More Workers** - In Dockerfile:
   ```dockerfile
   CMD ["gunicorn", "--workers", "8", ...]  # statt 4
   ```

2. **More Memory** - In UNRAID WebGUI:
   - Memory Limit erhöhen: 4GB statt 2GB

3. **SSD Cache** - Database auf Cache Pool:
   - `/mnt/cache/appdata/shopping-points-optimiser/instance`

4. **Redis Caching** - Optional hinzufügen:
   ```yaml
   redis:
     image: redis:7-alpine
     networks:
       - shopping-network
   ```

---

## 🔗 Zuverlässige Zugänge auf UNRAID

### Lokal im LAN
```
http://unraid-ip:5000/admin
http://unraid-ip:5000/  (Startseite)
```

### Von außen (mit Reverse Proxy + HTTPS)
```
https://shopping.yourdomain.com/admin
```

### Mit dynamischem DNS
Falls deine IP wechselt:
```
https://shopping.deine-ddns.com/admin
```

---

## 📚 Weitere UNRAID Tipps

**Sichern auf regelmäßig Backups:**
```bash
# Komplettes AppData Backup
tar -czf /mnt/user/backups/shopping_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  /mnt/user/appdata/shopping-points-optimiser/
```

**Docker Stats anschauen:**
```bash
docker stats shopping-points-optimiser
# Zeigt: CPU, Memory, Network Usage in Echtzeit
```

**Container automatisch bei Reboot starten:**
- UNRAID Dashboard: Container → Auto start: ON



---

## 📚 Weitere Ressourcen

- [Docker Dokumentation](https://docs.docker.com/)
- [UNRAID Docker Dokumentation](https://docs.unraid.net/unraid-os/advanced-topics/docker/docker-containers/)
- [Docker Compose Referenz](https://docs.docker.com/compose/compose-file/)
- [Shopping Points Optimiser README](../README.md)
- [GitHub Setup Guide](./GITHUB_SETUP.md)

---

## ❓ Häufige Fragen

**Q: Wie greife ich auf die Logs zu?**
```bash
docker logs shopping-points-optimiser -f
# -f = Follow (echtzeit)
# --tail 100 = Letzte 100 Zeilen
docker logs shopping-points-optimiser --tail 100
```

**Q: Kann ich ein Backup der Daten machen?**
Ja, immer!
```bash
# Vor großen Änderungen:
cp /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db \
   /mnt/user/appdata/shopping-points-optimiser/instance/shopping_points_backup.db

# Oder Snapshot via UNRAID (empfohlen)
```

**Q: Kann ich PostgreSQL statt SQLite verwenden?**
Ja, aber SQLite reicht für deine Größe. Später möglich via docker-compose Erweiterung.

**Q: Wo speichert UNRAID die Daten?**
- AppData: `/mnt/user/appdata/shopping-points-optimiser/instance/shopping_points.db`
- Ist persistent = überlebt Container Neustarts

**Q: Container wird nicht gestartet - was tun?**
1. Logs anschauen: `docker logs shopping-points-optimiser`
2. .env prüfen (SECRET_KEY gesetzt?)
3. Container Status: `docker ps -a | grep shopping`
4. Neu bauen und starten (siehe "Container startet nicht" oben)

**Q: Wie ändere ich den Port?**
```bash
# Container stoppen und mit anderem Port neu starten
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  -p 8080:5000 \
  --network shopping-network \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
# Dann: http://unraid-ip:8080/admin
```

**Q: Kann ich Systemressourcen limitieren?**
Ja, mit docker run Flags:
```bash
docker run -d \
  --name shopping-points-optimiser \
  --restart unless-stopped \
  --cpus="2" \
  --memory="2g" \
  --memory-reservation="1g" \
  -p 5000:5000 \
  --network shopping-network \
  -v /mnt/user/appdata/shopping-points-optimiser/instance:/app/instance \
  -v /mnt/user/appdata/shopping-points-optimiser/logs:/app/logs \
  --env-file .env \
  shopping-points-optimiser:latest
```

**Q: Wie aktualisiere ich das Projekt?**
```bash
cd /mnt/user/appdata/shopping-points-optimiser
docker stop shopping-points-optimiser
docker rm shopping-points-optimiser

# Altes Image entfernen (wichtig für neue Builds!)
docker rmi shopping-points-optimiser:latest

git pull origin main
docker build --no-cache -t shopping-points-optimiser:latest .

# Dann in UNRAID WebGUI: Docker Tab → Edit Container → Apply
```
Das stellt sicher, dass das neu gebaute Image verwendet wird!

---

## 🎯 Checkliste für Go-Live

- [ ] SECRET_KEY gesetzt und sicher (32+ Zeichen)
- [ ] ADMIN_PASSWORD stark (12+ Zeichen, Großbuchstaben, Zahlen, Sonderzeichen)
- [ ] DEBUG=False in .env
- [ ] .env ist NICHT in Git / im .gitignore
- [ ] Docker Image gebaut
- [ ] Container gestartet (automatische DB-Initialisierung läuft beim Start)
- [ ] Logs geprüft: `docker logs shopping-points-optimiser`
- [ ] Admin-Panel öffnet auf http://unraid-ip:5000/admin
- [ ] Login mit admin / ADMIN_PASSWORD funktioniert
- [ ] Backups konfiguriert
- [ ] Port 5000 im Firewall freigegeben (falls nötig)
- [ ] Auto-restart aktiviert (UNRAID WebGUI)
- [ ] Logs prüfen auf Fehler
