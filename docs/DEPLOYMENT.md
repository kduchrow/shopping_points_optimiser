# Production Deployment Guide

## Prerequisites

- Python 3.8+
- pip
- Virtual environment support
- Web server (nginx/Apache) for production

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3-pip python3-venv nginx -y

# Install Playwright dependencies
sudo playwright install-deps
```

### 2. Application Setup

```bash
# Clone repository
git clone <your-repo-url>
cd shopping_points_optimiser

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configuration

Create `.env` file:

```bash
FLASK_ENV=production
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///instance/shopping.db
```

### 4. Database Initialization

```bash
python scripts/reset_db.py
```

**⚠️ IMPORTANT:** Change default passwords immediately!

### 5. Production Server (Gunicorn)

```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/shopping-points.service
```

Service file:
```ini
[Unit]
Description=Shopping Points Optimiser
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/shopping_points_optimiser
Environment="PATH=/path/to/shopping_points_optimiser/.venv/bin"
ExecStart=/path/to/shopping_points_optimiser/.venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable shopping-points
sudo systemctl start shopping-points
```

### 6. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/shopping-points
```

Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/shopping_points_optimiser/static;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/shopping-points /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 8. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Maintenance

### Update Application

```bash
cd /path/to/shopping_points_optimiser
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart shopping-points
```

### Backup Database

```bash
# Backup
cp instance/shopping.db backups/shopping_$(date +%Y%m%d).db

# Restore
cp backups/shopping_20260105.db instance/shopping.db
sudo systemctl restart shopping-points
```

### Monitor Logs

```bash
# Application logs
sudo journalctl -u shopping-points -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Scheduled Scraping

Add to crontab:
```bash
crontab -e
```

```cron
# Run Miles & More scraper daily at 3 AM
0 3 * * * /path/to/.venv/bin/python /path/to/scripts/run_scraper.py miles_and_more

# Run Payback scraper daily at 4 AM
0 4 * * * /path/to/.venv/bin/python /path/to/scripts/run_scraper.py payback
```

## Security Checklist

- [ ] Change SECRET_KEY
- [ ] Change all default passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set up regular backups
- [ ] Enable rate limiting
- [ ] Review user permissions
- [ ] Set up monitoring

## Performance Optimization

1. **Database**: Consider PostgreSQL for production
2. **Caching**: Add Redis for session/cache management
3. **CDN**: Serve static files via CDN
4. **Workers**: Scale Gunicorn workers based on CPU cores

## Troubleshooting

### Service won't start
```bash
sudo systemctl status shopping-points
sudo journalctl -u shopping-points -n 50
```

### Database locked
```bash
# Check for running processes
ps aux | grep python
# Kill if necessary
sudo systemctl restart shopping-points
```

### Scraper fails
```bash
# Check Playwright installation
playwright install chromium
playwright install-deps
```

## Monitoring

Consider setting up:
- **Uptime monitoring**: UptimeRobot, Pingdom
- **Error tracking**: Sentry
- **Analytics**: Google Analytics
- **Performance**: New Relic, DataDog

## Support

For production issues, check:
1. Application logs (`journalctl`)
2. Nginx logs (`/var/log/nginx/`)
3. Database integrity
4. Disk space (`df -h`)
5. Memory usage (`free -m`)
