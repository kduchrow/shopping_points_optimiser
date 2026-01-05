# 🚀 Production Checklist

## Pre-Deployment

### Security
- [ ] Change `SECRET_KEY` in production
- [ ] Change all default passwords (admin, contributor, testuser, viewer)
- [ ] Review user permissions and roles
- [ ] Enable HTTPS/SSL certificate
- [ ] Configure firewall rules
- [ ] Set up rate limiting (if needed)
- [ ] Review and sanitize all user inputs

### Configuration
- [ ] Set `FLASK_ENV=production`
- [ ] Configure production database (consider PostgreSQL)
- [ ] Set up environment variables (`.env`)
- [ ] Configure logging
- [ ] Set up error monitoring (Sentry, etc.)
- [ ] Configure email settings (for notifications)

### Database
- [ ] Run database migrations
- [ ] Set up automated backups
- [ ] Test backup restoration process
- [ ] Configure database connection pooling
- [ ] Set up database monitoring

### Testing
- [ ] Run all unit tests (`pytest tests/`)
- [ ] Test scraper functionality
- [ ] Test notification system
- [ ] Test shop deduplication
- [ ] Load testing (if expected high traffic)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile responsiveness check

### Performance
- [ ] Enable caching (Redis recommended)
- [ ] Optimize database queries
- [ ] Configure CDN for static files
- [ ] Set up application monitoring
- [ ] Configure Gunicorn workers (2-4 × CPU cores)
- [ ] Enable gzip compression

### Documentation
- [ ] Review and update README.md
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Document deployment process
- [ ] Create troubleshooting guide

## Deployment

### Server Setup
- [ ] Install required system packages
- [ ] Install Python dependencies
- [ ] Install Playwright and browsers
- [ ] Configure web server (Nginx/Apache)
- [ ] Set up systemd service
- [ ] Configure reverse proxy

### Application
- [ ] Clone/upload application code
- [ ] Install Python dependencies
- [ ] Initialize database
- [ ] Run database seeding (if needed)
- [ ] Test application startup
- [ ] Verify all endpoints work

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error alerts
- [ ] Set up log aggregation
- [ ] Configure performance monitoring
- [ ] Set up security monitoring

## Post-Deployment

### Verification
- [ ] Verify application is accessible
- [ ] Test login functionality
- [ ] Run a test scraper job
- [ ] Test notification delivery
- [ ] Verify shop deduplication works
- [ ] Check database writes
- [ ] Test admin panel functionality

### Maintenance
- [ ] Schedule regular backups
- [ ] Set up cron jobs for scrapers
- [ ] Configure log rotation
- [ ] Plan for database maintenance
- [ ] Document maintenance procedures

### Support
- [ ] Set up support email/system
- [ ] Create admin contact list
- [ ] Document escalation procedures
- [ ] Set up status page (optional)

## Quick Deploy Commands

```bash
# 1. Server setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx -y

# 2. Clone and setup
git clone <repo-url>
cd shopping_points_optimiser
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 3. Configure
cp .env.example .env
nano .env  # Edit configuration

# 4. Database
python scripts/reset_db.py
# CHANGE DEFAULT PASSWORDS!

# 5. Test
python -m pytest tests/
python app.py  # Test startup

# 6. Deploy with Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 7. Configure Nginx and systemd (see DEPLOYMENT.md)
```

## Critical Warnings

⚠️ **NEVER use default passwords in production!**
⚠️ **ALWAYS change SECRET_KEY before deploying!**
⚠️ **ALWAYS use HTTPS in production!**
⚠️ **ALWAYS set up automated backups!**
⚠️ **NEVER commit .env files to git!**

## Support Contacts

- Technical Issues: [admin@example.com](mailto:admin@example.com)
- Security Issues: [security@example.com](mailto:security@example.com)
- Documentation: `docs/` folder

---

**Last Updated:** 2026-01-05
